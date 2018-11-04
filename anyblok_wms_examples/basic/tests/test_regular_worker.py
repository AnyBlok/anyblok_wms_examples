# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok / WMS Examples project
#
#    Copyright (C) 2018 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok_wms_base.testing import WmsTestCase


class RegularWorkerTestCase(WmsTestCase):

    def setUp(self):
        super().setUp()
        Wms = self.Wms = self.registry.Wms
        self.assertEqual(self.Wms.Reservation.query().count(), 0)
        self.Worker = Wms.Worker.Regular
        self.PhysObj = Wms.PhysObj
        self.Operation = Wms.Operation
        self.Arrival = Wms.Operation.Arrival

    def gt_by_code(self, code):
        return self.single_result(self.PhysObj.Type.query().filter_by(
            code=code))

    def test_missing_product(self):
        # to avoid pollution, we restrict the query to just one product
        query = '\n'.join((self.Worker.missing_product_query(),
                           "AND product='%s'"))
        worker = self.Worker()
        # yes, usually string formatting of queries is evil, but I'll wrestle
        # with SQLA param passing in that case later (doesn't matter much in
        # this test code)
        self.assertEqual(
            self.registry.execute(query % 'JEANS/31/31').rowcount,
            1)
        for code in (('JEANS/31/31', 'JEANS/31/32/PCK')):
            self.Arrival.create(goods_type=self.gt_by_code(code),
                                timeslice=1,
                                location=worker.incoming_location,
                                state='done')
        for product in ('JEANS/31/31', 'JEANS/31/32'):
            self.assertEqual(
                len(self.registry.execute(query % product).fetchall()),
                0)

    def test_purchase(self):
        worker = self.Worker(done_timeslice=1)
        pack_code = worker.purchase()

        self.assertIsNotNone(pack_code)
        resa = self.single_result(self.Wms.Reservation.query())
        request = resa.request_item.request
        self.assertEqual(request.purpose, "unpack")
        self.assertEqual(resa.physobj.type.code, pack_code)

        Arrival = self.Wms.Operation.Arrival
        arrival = self.single_result(Arrival.query())
        self.assertEqual(arrival.goods_type.code, pack_code)
        self.assertEqual(arrival.timeslice, 4)

    def test_purchase_not_needed(self):
        worker = self.Worker()
        worker.missing_product_query = lambda: (
            "SELECT product FROM wms_physobj_type WHERE id=id+1")
        self.assertFalse(worker.purchase())

    def test_process_arrival(self):
        worker = self.Worker.insert()
        pack_code = worker.purchase()

        worker.done_timeslice += 2
        self.assertTrue(worker.process_arrival())

        PhysObj = self.Wms.PhysObj
        Avatar = PhysObj.Avatar
        phobj = self.single_result(PhysObj.query().join(PhysObj.type).filter(
            PhysObj.Type.code == pack_code))
        avatar = self.single_result(Avatar.query().filter_by(state='present',
                                                             obj=phobj))
        self.assertEqual(avatar.location.code, 'incoming')

        # no more to be done
        self.assertFalse(worker.process_arrival())

    def test_process_unpack(self):
        regular = self.Worker()
        planner = self.Wms.Worker.Planner.insert()

        regular.purchase()
        planner.process_one()

        Operation = self.Wms.Operation
        for arrival in Operation.Arrival.query().all():
            arrival.execute()

        orig_commit = regular.registry.commit
        regular.registry.commit = lambda: None
        try:
            self.assertEqual(regular.process_one()[0],
                             'Model.Wms.Operation.Move')
            unpack_info = regular.process_one()
        finally:
            regular.registry.commit = orig_commit
        self.assertEqual(unpack_info[0], 'Model.Wms.Operation.Unpack')
        unpack_op = Operation.query().get(unpack_info[1])
        for av in unpack_op.outcomes:
            self.assertEqual(av.state, 'present')
