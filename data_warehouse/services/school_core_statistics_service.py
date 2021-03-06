'''school core statistics service'''
from datetime import timedelta
from django.core.cache import cache
from django.db import models
from django.db.models import Count, functions
from django.utils.timezone import now, localtime

from training_event.models import CampusEvent
from training_record.models import Record
from auth.services import UserService


class SchoolCoreStatisticsService:
    '''Provide access to school' core statistics data.'''
    @staticmethod
    def get_events_statistics():
        '''Populate events statistics for whole school.

        Return
        ------
        data: dict
            {
                timestamp: datetime
                    The time when this data was generated.
                available_to_enroll: int
                    The number of events which are available to enroll.
            }
        '''
        cache_key = 'events_statistics'
        cached_value = cache.get(cache_key)
        if cached_value:
            return cached_value
        current_time = localtime(now())
        res = {
            'timestamp': current_time,
            'available_to_enroll': (
                CampusEvent.objects.filter(
                    deadline__gt=current_time, reviewed=True).count()
            ),
        }
        cache.set(cache_key, res, 8 * 3600)
        return res

    @staticmethod
    def get_records_statistics():
        '''Populate records statistics for whole school.

        Return
        ------
        data: dict
            {
                timestamp: datetime
                    The time when this data was generated.
                num_records: int
                    The total number of records
                num_records_added_in_current_month: int
                    The number of records added in this month
                num_average_records: float
                    The average number of records per user
            }
        '''
        cache_key = 'records_statistics'
        cached_value = cache.get(cache_key)
        if cached_value:
            return cached_value
        current_time = localtime(now())

        # The total number of records
        num_records = Record.valid_objects.count()

        # The number of records added in this month
        num_records_added_in_current_month = (
            Record.valid_objects
            .filter(create_time__gte=current_time.replace(
                day=1, hour=0, minute=0, second=0))
            .count()
        )

        num_users = UserService.get_full_time_teachers().count()
        num_average_records = num_records / num_users if num_users else 0
        res = {
            'timestamp': current_time,
            'num_records': num_records,
            'num_records_added_in_current_month': (
                num_records_added_in_current_month
            ),
            'num_average_records': num_average_records
        }
        cache.set(cache_key, res, 8 * 3600)
        return res

    @staticmethod
    def get_department_records_statistics():
        '''Populate records statistics for departments in current year.

        Return
        ------
        data: dict
            {
                timestamp: datetime
                    The time when this data was generated.
                data : dict
                    {
                        department: str
                            The name of the department
                        num_users: int
                            The number of users in this department
                        num_records: int
                            The number of records created in this department
                            in this year
                    }
        '''
        cache_key = 'department_records_statistics'
        cached_value = cache.get(cache_key)
        if cached_value:
            return cached_value
        current_time = localtime(now())
        grouped_counts = (
            Record.valid_objects
            .filter(create_time__gte=current_time.replace(
                month=1, day=1, hour=0, minute=0, second=0))
            .annotate(
                department_name=models.F(
                    'user__administrative_department__name'
                )
            )
            .values('department_name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        grouped_users = {x['department_name']: x['count'] for x in (
            UserService.get_full_time_teachers()
            .annotate(
                department_name=models.F('administrative_department__name'))
            .values('department_name')
            .annotate(count=Count('id'))
        )}
        data = []
        for item in grouped_counts:
            department_name = item['department_name']
            num_records = item['count']
            num_users = grouped_users.get(department_name, 0)
            data.append({
                'department': department_name,
                'num_users': num_users,
                'num_records': num_records,
            })
        res = {
            'timestamp': current_time,
            'data': data
        }
        cache.set(cache_key, res, 8 * 3600)
        return res

    @staticmethod
    def get_monthly_added_records_statistics():
        '''Populate records statistics for recent 12 months.'''
        cache_key = 'monthly_added_records_statistics'
        cached_value = cache.get(cache_key)
        if cached_value:
            return cached_value
        current_time = now().replace(day=30)
        start_time = current_time.replace(year=current_time.year-1, day=1,
                                          hour=0, minute=0, second=0)

        def format_time(dt_instance):
            return dt_instance.strftime('%Y年%m月')

        monthly_records = {format_time(x['month']): x['count'] for x in (
            Record.valid_objects
            .filter(create_time__gte=start_time)
            .annotate(
                month=functions.TruncMonth('create_time'),
            )
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )}
        months = []
        tmp_time = start_time
        while tmp_time <= current_time:
            months.append(format_time(tmp_time))
            tmp_time += timedelta(days=31)
        res = {
            'timestamp': current_time,
            'months': months,
            'records': [monthly_records.get(x, 0) for x in months]
        }
        cache.set(cache_key, res, 8 * 3600)
        return res
