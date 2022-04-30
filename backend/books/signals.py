from django import dispatch

post_create_issue = dispatch.Signal(providing_args=['instance'])
