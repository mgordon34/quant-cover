from sqlalchemy import JSON, BigInteger, Integer
from sqlalchemy.dialects.postgresql import JSONB

portable_bigint = BigInteger().with_variant(Integer, "sqlite")
portable_json = JSONB().with_variant(JSON, "sqlite")
