from __future__ import absolute_import, division, print_function

import smtplib

import e3.net.smtp

import mock


def test_sendmail():
    from_addr = 'e3@example.net'
    to_addresses = ['info@example.net', 'info@example.com']
    msg_as_string = 'test mail content'
    with mock.patch('smtplib.SMTP') as mock_smtp:
        e3.net.smtp.sendmail(
            from_addr,
            to_addresses,
            msg_as_string,
            ['smtp.localhost'])

        smtp_mock = mock_smtp.return_value
        assert smtp_mock.sendmail.called
        assert smtp_mock.sendmail.call_count == 1
        smtp_mock.sendmail.assert_called_once_with(
            from_addr,
            to_addresses,
            msg_as_string)


def test_sendmail_onerror():
    from_addr = 'e3@example.net'
    to_addresses = ['info@example.net', 'info@example.com']
    msg_as_string = 'test mail content'
    msg_size_exceed = "A" * 1200
    result = e3.net.smtp.sendmail(
        from_addr,
        to_addresses,
        msg_size_exceed,
        ['smtp.localhost'],
        max_size=8 / 1024)
    assert result is False

    with mock.patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = smtplib.SMTPException()
        result = e3.net.smtp.sendmail(
            from_addr,
            to_addresses,
            msg_as_string,
            ['smtp.localhost'])
        assert result is False

    with mock.patch('smtplib.SMTP') as mock_smtp:
        smtp_mock = mock_smtp.return_value
        smtp_mock.sendmail.side_effect = smtplib.SMTPException()
        result = e3.net.smtp.sendmail(
            from_addr,
            to_addresses,
            msg_as_string,
            ['smtp.localhost'])
        assert result is False

    with mock.patch('smtplib.SMTP') as mock_smtp:
        smtp_mock = mock_smtp.return_value
        smtp_mock.sendmail.return_value = {}
        result = e3.net.smtp.sendmail(
            from_addr,
            to_addresses,
            msg_as_string,
            ['smtp.localhost'])
        assert result is True
