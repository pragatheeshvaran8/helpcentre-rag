"""Observability: what the app records about itself, and how you search it.

In production nobody is watching. The app has to watch itself, or a customer
saying "it told me something wrong yesterday" is unanswerable.

Three files:

    trace.py   what is recorded for every request, and how a run is replayed
    store.py   where it goes, and how it is read back
    search.py  the support drill: finding one bad answer from a vague complaint
"""
