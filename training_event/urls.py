'''Register URL routes in training_event module.'''
from rest_framework import routers

import training_event.views


router = routers.SimpleRouter()
router.register(r'campus-events', training_event.views.CampusEventViewSet)
router.register(r'off-campus-events',
                training_event.views.OffCampusEventViewSet)
router.register(r'enrollments', training_event.views.EnrollmentViewSet)
urlpatterns = router.urls