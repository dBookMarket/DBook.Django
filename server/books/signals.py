from django import dispatch

sig_issue_new_book = dispatch.Signal(providing_args=['instance'])
