"""
DATABASE BASE MODEL & PROXY
===========================
Base Peewee ORM database proxy and model base class.
"""

from __future__ import annotations

from peewee import AutoField, Model, Proxy

# Database Proxy allows swapping connection at runtime (e.g. for testing)
db = Proxy()


class BaseModel(Model):
    id = AutoField()

    class Meta:
        database = db
