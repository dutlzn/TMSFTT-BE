'''Provide services of training event module.'''
from itertools import chain
import tempfile

import xlwt
from django.db import transaction
from django.utils.timezone import now

from infra.utils import prod_logger
from infra.exceptions import BadRequest
from training_event.models import CampusEvent, Enrollment, EventCoefficient
from training_record.models import Record
from auth.models import User
from auth.services import PermissionService


class CampusEventService:
    '''Provide services for CampusEvent.'''
    @staticmethod
    def review_campus_event(event, user):
        '''Review a campus event.'''
        event.reviewed = True
        event.save()

        msg = f'用户 {user} 将培训活动 {event} 标记为已审核'
        prod_logger.info(msg)

    @staticmethod
    def create_campus_event(validated_data, coefficients, context=None):
        '''Create a CampusEvent with ObjectPermission.

        Parametsers
        ----------
        validated_data: dict
            This dict should have full information needed to
            create an CampusEvent.
        coefficients: list
            An optional list to provide event_coefficient about
            expert information and participator information.
        context: dict
            An optional dict to provide contextual information. Default: None

        Returns
        -------
        campus_event: CampusEvent
        '''
        with transaction.atomic():
            campus_event = CampusEvent.objects.create(**validated_data)
            PermissionService.assign_object_permissions(
                context['request'].user, campus_event)
            for coefficient in coefficients:
                EventCoefficient.objects.create(campus_event=campus_event,
                                                **coefficient)

            return campus_event


class EnrollmentService:
    '''Provide services for Enrollment.'''
    @staticmethod
    def create_enrollment(enrollment_data):
        '''Create a enrollment for specific campus event.

        This action is atomic, will fail if there are no more heads counts for
        the campus event or duplicated enrollments are created.

        Parametsers
        ----------
        enrollment_data: dict
            This dict should have full information needed to
            create an Enrollment.

        Returns
        -------
        enrollment: Enrollment
        '''
        with transaction.atomic():
            # Lock the event until the end of the transaction
            event = CampusEvent.objects.select_for_update().get(
                id=enrollment_data['campus_event'].id)
            if event.num_enrolled >= event.num_participants:
                raise BadRequest('报名人数已满')

            enrollment = Enrollment.objects.create(**enrollment_data)
            # Update the number of enrolled participants
            event.num_enrolled += 1
            event.save()
            PermissionService.assign_object_permissions(
                enrollment_data['user'], enrollment)

            return enrollment

    @staticmethod
    def delete_enrollment(instance):
        """Provide services for delete enrollments.
        Parameters
        ----------
        instance: enrollment
            删除的enrollment对象
        """
        with transaction.atomic():
            # Lock the event until the end of the transaction
            event = CampusEvent.objects.select_for_update().get(
                id=instance.campus_event_id
            )
            event.num_enrolled -= 1
            event.save()
            instance.delete()

    @staticmethod
    def get_user_enrollment_status(events, user):
        """Provide services for get Enrollment Status.
        Parameters
        ----------
        events: list
            要查询的校内活动的对象列表或者数字列表
        user: number or object
            当然的用户的id或者对象


        Returns
        -------
        result: dict
        key 为活动的编号
        value 活动是否报名，True表示该活动已经报名，False表示活动没有报名
        """
        if events and isinstance(events[0], CampusEvent):
            events = [event.id for event in events]

        enrolled_events = set(Enrollment.objects.filter(
            user=user, campus_event__id__in=events
        ).values_list('campus_event_id', flat=True))

        return {event: event in enrolled_events
                for event in events}

    @staticmethod
    def get_user_enrollment_id(events, user):
        """Provide services for get Enrollment id.
        Parameters
        ----------
        events: list
            要查询的校内活动的对象列表或者数字列表
        user: number or object
            当然的用户的id或者对象


        Returns
        -------
        result: dict
        key 为活动的编号
        value 如果活动报名，value是报名的id，如果活动没有报名，value就是None
        """
        if events and isinstance(events[0], CampusEvent):
            events = [event.id for event in events]

        enrolled_data = dict(Enrollment.objects.filter(
            user=user, campus_event__id__in=events
        ).values_list('campus_event_id', 'id'))

        return {event: enrolled_data[event] if event in enrolled_data else None
                for event in events}


class CoefficientCalculationService:
    '''Provide workload calculation method .'''

    WORKLOAD_SHEET_NAME = '工作量汇总统计'
    WORKLOAD_SHEET_TITLE = ['序号', '学部（学院）', '教师姓名', '工作量']
    WORKLOAD_SHEET_TITLE_STYLE = ('font: bold on; '
                                  'align: wrap on, vert centre, horiz center'
                                  )

    @staticmethod
    def calculate_workload_by_query(administrative_department=None,
                                    start_time=None, end_time=None,
                                    teachers=None):
        """calculate workload by department and period

        Parameters
        ----------
        start_time: date
            查询起始时间
        end_time: date
            查询结束时间
        department: Department
            查询的学院
        teachers: list of users, optional
            可选参数，list中存储需要查询的老师，该参数与department互斥，当二者
            同时存在时，以teachers参数查询为主，department参数不生效
        Returns
        -------
        result: dict
            key 为学部老师
            values 为该老师在规定查询时间段内的工时
        """
        if end_time is None:
            end_time = now()
        if start_time is None:
            start_time = end_time.replace(month=1, day=1, hour=0, minute=0,
                                          second=0)
        if teachers is None:
            teachers = User.objects.exclude(
                administrative_department__isnull=True)
            if administrative_department is not None:
                teachers = teachers.filter(
                    administrative_department=administrative_department)
        campus_records = Record.objects.select_related(
            'event_coefficient', 'user',
            'user__administrative_department').filter(
                user__in=teachers,
                campus_event__time__gte=start_time,
                campus_event__time__lte=end_time)

        off_campus_records = Record.objects.select_related(
            'event_coefficient', 'user',
            'user__administrative_department').filter(
                user__in=teachers, off_campus_event__time__gte=start_time,
                off_campus_event__time__lte=end_time)
        result = {}
        for record in chain(campus_records, off_campus_records):
            user = record.user
            result.setdefault(user, 0)
            result[user] += (
                record.event_coefficient.calculate_event_workload(record)
            )

        return result

    @staticmethod
    def generate_workload_excel_from_data(workload_dict):
        """ 根据传入的工作量汇总字典生成excel

        Parameters
        ----------
        workload_dict: dict
            key 为user，value为对应user的工作量，通过调用
            calculate_workload_by_query方法获取相应字典
        Returns
        -------
        file_path: str
        """

        # 初始化excel
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(
            CoefficientCalculationService.WORKLOAD_SHEET_NAME)
        style = xlwt.easyxf(
            CoefficientCalculationService.WORKLOAD_SHEET_TITLE_STYLE)
        # 生成表头
        for col, title in enumerate(
                CoefficientCalculationService.WORKLOAD_SHEET_TITLE):
            worksheet.write(0, col, title, style)

        # 根据学院名排序，优化输出形式
        workload_list = sorted(
            workload_dict.items(),
            key=lambda item: item[0].administrative_department.name)
        # 写数据
        for row, teacher in enumerate(workload_list):

            worksheet.write(row+1, 0, row+1)
            worksheet.write(row+1, 1,
                            teacher[0].administrative_department.name)
            worksheet.write(row+1, 2, teacher[0].first_name)
            worksheet.write(row+1, 3, teacher[1])

        _, file_path = tempfile.mkstemp()

        workbook.save(file_path)
        return file_path
