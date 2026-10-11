from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from database import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True)
    name = Column(String(150), nullable=False)
    legal_name = Column(String(200))
    tax_id = Column(String(20))
    email = Column(String(150))
    phone = Column(String(30))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class CompanyUserModel(Base):
    __tablename__ = "company_users"

    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False)

    company = relationship("CompanyModel")
    user = relationship("UserModel")


class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    account_type = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    bank_name = Column(String(150))
    account_number = Column(String(50))
    clabe = Column(String(18))
    card_last_digits = Column(String(4))
    short_description = Column(String(255))
    long_description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    company = relationship("CompanyModel")


class ConceptModel(Base):
    __tablename__ = "concepts"

    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    concept_type = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    short_description = Column(String(255))
    long_description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class AccountConceptModel(Base):
    __tablename__ = "account_concepts"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)

    account = relationship("AccountModel")
    concept = relationship("ConceptModel")


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    captured_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    captured_at = Column(DateTime, nullable=False)
    short_description = Column(String(255))
    long_description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    account = relationship("AccountModel")
    concept = relationship("ConceptModel")
    captured_by_user = relationship("UserModel")


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)


class PermissionModel(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    role = relationship("RoleModel")
    permission = relationship("PermissionModel")


class CompanyUserRoleModel(Base):
    __tablename__ = "company_user_roles"

    id = Column(Integer, primary_key=True, index=True)
    company_user_id = Column(String(36), ForeignKey("company_users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    company_user = relationship("CompanyUserModel")
    role = relationship("RoleModel")
