'''Unit tests for training_event services.'''
import xlrd
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.timezone import now
from django.http import HttpRequest
from model_mommy import mommy
from infra.exceptions import BadRequest
from training_event.models import (
    CampusEvent, Enrollment, EventCoefficient, OffCampusEvent)
from training_event.services import (
    EnrollmentService, CoefficientCalculationService, CampusEventService)
from training_program.models import Program
from training_record.models import Record
from auth.models import Department
from auth.utils import assign_perm

User = get_user_model()


class TestCampusEventService(TestCase):
    '''Test services provided by CampusEventService.'''
    def setUp(self):
        self.user = mommy.make(User)
        self.group = mommy.make(Group, name="创新创业学院-管理员")
        self.depart = mommy.make(Department, name="创新创业学院")
        self.user.groups.add(self.group)
        program = mommy.make(Program)
        self.data = {
            "name": "1",
            "time": "2018-05-07T11:11:00+08:00",
            "location": "1",
            "num_hours": 1.0,
            "num_participants": 1,
            "deadline": "2019-05-09T01:11:00+08:00",
            "description": "1",
            "program": program,
        }
        self.request = HttpRequest()
        self.request.user = self.user
        self.context = {'request': self.request, 'data': ''}
        mommy.make(Group, name="大连理工大学-专任教师")
        assign_perm('training_program.add_program', self.group)
        assign_perm('training_program.view_program', self.group)

    def test_create_campus_event_admin(self):
        '''Should create campus_event.'''
        coefficient_expect = {
            'role': 1,
            'coefficient': 1,
            'hours_option': 1,
            'workload_option': 1,
        }
        coefficient_participator = {
            'role': 0,
            'coefficient': 1,
            'hours_option': 1,
            'workload_option': 1,
        }
        CampusEventService.create_campus_event(self.data,
                                               coefficient_expect,
                                               coefficient_participator,
                                               self.context)
        count_program = Program.objects.all().count()
        count_event_coefficient = EventCoefficient.objects.all().count()
        self.assertEqual(count_program, 1)
        self.assertEqual(count_event_coefficient, 2)


class TestEnrollmentService(TestCase):
    '''Test services provided by EnrollmentService.'''
    def setUp(self):
        self.event = mommy.make(CampusEvent, num_participants=0)
        self.user = mommy.make(User)
        self.group = mommy.make(Group, name="大连理工大学-专任教师")
        self.user.groups.add(self.group)
        self.data = {'campus_event': self.event, 'user': self.user}
        assign_perm('training_event.add_enrollment', self.group)
        assign_perm('training_event.delete_enrollment', self.group)

    def test_create_enrollment_no_more_head_counts(self):
        '''Should raise BadRequest if no more head counts for CampusEvent.'''
        with self.assertRaisesMessage(
                BadRequest, '报名人数已满'):
            EnrollmentService.create_enrollment(self.data)

    def test_create_enrollment_user_in_data(self):
        '''Should create enrollment.'''
        self.event.num_participants = 10
        self.event.save()
        EnrollmentService.create_enrollment(self.data)

        count = Enrollment.objects.filter(user=self.user).count()

        self.assertEqual(count, 1)

    def test_get_user_enrollment_status(self):
        '''Should get user enrollment status.'''
        events = [mommy.make(CampusEvent) for _ in range(10)]
        expected_result = {}
        for idx, event in enumerate(events):
            if idx >= 3:
                mommy.make(Enrollment, user=self.user, campus_event=event)
                expected_result[event.id] = True
            else:
                expected_result[event.id] = False
        results = EnrollmentService.get_user_enrollment_status(
            events, self.user.id)
        self.assertEqual(results, expected_result)

    def test_get_user_enrollment_id(self):
        '''Should get user enrollment id.'''
        events = [mommy.make(CampusEvent) for _ in range(10)]
        expected_result = {}
        for idx, event in enumerate(events):
            if idx >= 3:
                obj = mommy.make(Enrollment, user=self.user,
                                 campus_event=event)
                expected_result[event.id] = obj.id
            else:
                expected_result[event.id] = None

        results = EnrollmentService.get_user_enrollment_id(
            events, self.user.id)
        self.assertEqual(results, expected_result)

    def test_delete_enrollment(self):
        '''Should delete enrollment.'''
        self.event.num_participants = 10
        self.event.num_enrolled = 2
        self.event.save()
        enrollment = mommy.make(Enrollment,
                                user=self.user, campus_event=self.event)
        EnrollmentService.delete_enrollment(enrollment)
        self.assertEqual(Enrollment.objects.count(), 0)


class TestCoefficientCalculationService(TestCase):
    '''Test services provided by EnrollmentService.'''
    NUM_HOURS = 10
    RECORDS_NUMS = 10

    @classmethod
    def setUpTestData(cls):

        cls.off_campus_event = mommy.make(OffCampusEvent, time=now())
        cls.campus_event = mommy.make(CampusEvent, num_hours=cls.NUM_HOURS,
                                      time=now())
        cls.department = mommy.make(Department)
        cls.user = mommy.make(User, department=cls.department,
                              administrative_department=cls.department)
        cls.event_coefficient = mommy.make(
            EventCoefficient, campus_event=cls.campus_event, coefficient=1,
            hours_option=EventCoefficient.ROUND_METHOD_CEIL,
            workload_option=EventCoefficient.ROUND_METHOD_CEIL,)

        cls.campus_records = [mommy.make(
            Record, event_coefficient=cls.event_coefficient, user=cls.user,
            campus_event=cls.campus_event) for _ in range(cls.RECORDS_NUMS)]

        cls.off_campus_record = mommy.make(
            Record, event_coefficient=cls.event_coefficient,
            off_campus_event=cls.off_campus_event, user=cls.user)
        cls.workload = 100
        cls.workload_dict = {cls.user: cls.workload}
        cls.filename = 'testfile'

    def test_calculate_workload_by_query(self):
        '''Should return workload by query'''
        self.assertEqual(
            CoefficientCalculationService.calculate_workload_by_query(
                administrative_department=self.department)[self.user],
            self.NUM_HOURS * self.RECORDS_NUMS)

    def test_generate_workload_excel_from_data(self):
        '''Should generate excel correctly'''
        path = (CoefficientCalculationService
                .generate_workload_excel_from_data(self.workload_dict)
                )
        workbook = xlrd.open_workbook(path)
        sheet = workbook.sheet_by_name(
            CoefficientCalculationService.WORKLOAD_SHEET_NAME)
        row = 0
        for col, title in enumerate(
                CoefficientCalculationService.WORKLOAD_SHEET_TITLE):
            self.assertEqual(title, sheet.cell_value(row, col))
        row += 1
        self.assertEqual(sheet.cell_value(row, 0), row)
        self.assertEqual(sheet.cell_value(row, 1), self.user.department.name)
        self.assertEqual(sheet.cell_value(row, 2), self.user.first_name)
        self.assertEqual(sheet.cell_value(row, 3), self.workload)
