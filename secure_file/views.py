'''Provide views for secure_file module.'''
from django.shortcuts import get_object_or_404
from django.apps import apps
from rest_framework import views, viewsets, exceptions

from secure_file.utils import (
    generate_download_response, decrypt_file_download_url
)
from secure_file.models import InSecureFile
from infra.exceptions import BadRequest
from infra.utils import dev_logger, prod_logger


class InSecuredFileDownloadView(views.APIView):
    '''Provide access for insecure files.'''
    def get(self, request, file_id):
        '''Serve insecure file.'''
        if not file_id.isdigit():
            raise exceptions.NotFound()
        file_id = int(file_id)
        try:
            field_file = InSecureFile.objects.get(id=file_id).path
        except InSecureFile.DoesNotExist:
            raise exceptions.NotFound()
        return generate_download_response(request, field_file, logging=False)


class SecuredFileDownloadView(views.APIView):
    '''Provide logic for downloading files.

    This type of secured url is implicitly generated by SecureFileField() of a
    serializer, or explicitly generated by
    SecureFile.generate_download_response().
    '''
    # pylint: disable=too-many-arguments
    def _verify_validity(self, request, model_name,
                         field_name, path, perm_name):
        '''Verify validity of the request.'''
        lookups = {field_name: path}
        instance = get_object_or_404(apps.get_model(model_name), **lookups)
        real_file = getattr(instance, field_name, None)
        if real_file is None or real_file.name != path:
            msg = f'文件路径无效: {path}'
            dev_logger.info(msg)
            raise exceptions.NotFound()
        if not request.user.has_perm(perm_name, instance):
            # If user has no permission, we simply return 404
            msg = (
                f'用户 {request.user.first_name}'
                f'(用户名: {request.user.username}) '
                f'尝试访问无权限文件: {path}'
            )
            prod_logger.info(msg)
            raise exceptions.NotFound()
        return real_file

    def get(self, request, encrypted_url):
        '''Decrypt, verify download request and redirect to download.'''
        try:
            (model_name, field_name,
             path, perm_name) = decrypt_file_download_url(encrypted_url)
        except Exception as exc:
            msg = f'加密链接解码失败: {exc}'
            dev_logger.info(msg)
            raise exceptions.NotFound()
        field_file = self._verify_validity(
            request, model_name, field_name, path, perm_name)
        return generate_download_response(request, field_file)


class InSecureFileViewSet(viewsets.ViewSet):
    '''Provide access to upload or download in-secure files.'''
    def create(self, request):
        '''Generate InSecureFile from request return url for accessing it.'''
        uploaded_file = request.FILES.get('upload', None)
        if uploaded_file is None:
            raise BadRequest('请指定上传文件')
        insecure_file = InSecureFile.from_path(
            request.user, uploaded_file.name, uploaded_file)
        return insecure_file.generate_download_response(request)
