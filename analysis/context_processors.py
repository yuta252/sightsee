"""
    Define data to send to Template
"""

def common(request):
    user = request.user
    context = {
        'user':user,
    }
    return context