'''Define ORM models for infra module.'''
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy as _f


User = get_user_model()


class OperationLog(models.Model):
    '''OperationLog holds details about critical operations.'''
    HTTP_METHODS = (
        (0, 'GET'),
        (1, 'POST'),
        (2, 'PUT'),
        (3, 'PATCH'),
        (4, 'DELETE'),
        (5, 'HEAD'),
        (6, 'OPTIONS'),
        (7, 'TRACE'),
    )
    # The dict is used to lookup method val given method name.
    # e.g. HTTP_METHODS_DICT['POST'] will give 1.
    HTTP_METHODS_DICT = {method_name: method_val
                         for method_val, method_name in HTTP_METHODS}

    class Meta:
        verbose_name = _('操作日志')
        verbose_name_plural = _('操作日志')
        default_permissions = ()
        permissions = (
            ('add_operationlog', '允许添加操作日志'),
            ('view_operationlog', '允许查看操作日志'),
            ('change_operationlog', '允许修改操作日志'),
            ('delete_operationlog', '允许删除操作日志'),
        )

    time = models.DateTimeField(verbose_name=_('操作时间'), auto_now_add=True)
    remote_ip = models.GenericIPAddressField(verbose_name=_('操作来源IP'))
    requester = models.ForeignKey(User, verbose_name=_('操作人员'),
                                  on_delete=models.PROTECT)
    method = models.PositiveSmallIntegerField(verbose_name=_('HTTP方法'),
                                              choices=HTTP_METHODS)
    url = models.URLField(verbose_name=_('请求URL'), max_length=256)
    referrer = models.URLField(verbose_name=_('来源URL'), max_length=256)
    user_agent = models.CharField(verbose_name=_('用户代理标识'),
                                  max_length=256)

    def __str__(self):
        return '{}({} {} {})'.format(self.time, self.requester_id,
                                     self.method, self.url)


class Notification(models.Model):
    '''Notification is sent by admins and received by users.'''
    class Meta:
        verbose_name = _('通知')
        verbose_name_plural = _('通知')
        default_permissions = ()
        permissions = (
            ('add_notification', '允许添加通知'),
            ('view_notification', '允许查看通知'),
            ('change_notification', '允许修改通知'),
            ('delete_notification', '允许删除通知'),
        )

    time = models.DateTimeField(verbose_name=_('发送时间'), auto_now_add=True)
    sender = models.ForeignKey(User, verbose_name=_('发送者'),
                               related_name='notifications_sent',
                               on_delete=models.PROTECT)
    recipient = models.ForeignKey(User, verbose_name=_('接收者'),
                                  related_name='notifications_received',
                                  on_delete=models.PROTECT)
    content = models.CharField(verbose_name=_('内容'), max_length=512)
    read_time = models.DateTimeField(verbose_name=_('阅读时间'),
                                     blank=True, null=True)

    def __str__(self):
        return str(_f('由{}于{}发送给{}的通知({})',
                      self.sender_id, self.time, self.recipient_id,
                      _('已读') if self.read_time else _('未读')))
