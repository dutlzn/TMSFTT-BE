'''Unit tests for training_review models.'''
from django.test import TestCase

from training_review.models import ReviewNote


class TestReviewNote(TestCase):
    '''Unit tests for model ReviewNote.'''
    def test_str(self):
        '''Should render string correctly.'''
        user_id = 123
        record_id = 456
        expected_str = '由{}创建的关于{}的审核提示'.format(user_id, record_id)

        note = ReviewNote(user_id=user_id, record_id=record_id)

        self.assertEqual(str(note), str(expected_str))
