import re
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal as PyDecimal
from enum import Enum
from typing import Optional

import bcrypt
import strawberry

from database import Base, SessionLocal, engine
from models import (
    AccountConceptModel, AccountModel, CompanyModel, CompanyUserModel, CompanyUserRoleModel,
    ConceptModel, PermissionModel, RoleModel, RolePermissionModel, TransactionModel, UserModel,
)

Time = strawberry.scalar(
    datetime, name="Time",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: datetime.fromisoformat(v),
)
Decimal = strawberry.scalar(
    PyDecimal, name="Decimal",
    serialize=lambda v: float(v),
    parse_value=lambda v: PyDecimal(str(v)),
)


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def int_id(value) -> int:
    return int(value) if str(value).isdigit() else 0


def valid_email(email: str) -> bool:
    return bool(email) and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip())



#  Company, User, CompanyUser


@strawberry.type
class Company:
    id: strawberry.ID
    name: str
    legal_name: Optional[str]
    tax_id: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time


@strawberry.type
class User:
    id: strawberry.ID
    name: str
    email: str
    hashed_password: strawberry.Private[str]
    email_verified: bool
    is_active: bool
    created_at: Time
    updated_at: Time


@strawberry.type
class Role:
    id: strawberry.ID
    code: str
    name: str
    description: Optional[str]
    is_active: bool


@strawberry.type
class Permission:
    id: strawberry.ID
    code: str
    name: str
    description: Optional[str]
    is_active: bool


@strawberry.type
class CompanyUser:
    id: strawberry.ID
    is_admin: bool
    is_active: bool
    joined_at: Time
    company: Company
    user: User
    role: Optional[Role]

    @strawberry.field
    def company_id(self) -> strawberry.ID:
        return self.company.id

    @strawberry.field
    def user_id(self) -> strawberry.ID:
        return self.user.id


@strawberry.type
class RolePermission:
    id: strawberry.ID
    role: Role
    permission: Permission
    is_active: bool


@strawberry.type
class CompanyUserRole:
    id: strawberry.ID
    company_user: CompanyUser
    role: Role
    is_active: bool


@strawberry.type
class AuthUser:
    id: strawberry.ID
    name: str
    email: str


@strawberry.type
class AuthPayload:
    token: str
    token_type: str
    user: AuthUser


@strawberry.input
class CreateCompanyInput:
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@strawberry.input
class UpdateCompanyInput:
    id: strawberry.ID
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class CreateCompanyAdminInput:
    company_id: strawberry.ID
    name: str
    email: str
    password: str


@strawberry.input
class CreateCompanyUserInput:
    company_id: strawberry.ID
    name: str
    email: str
    password: str


@strawberry.input
class CreateRoleInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.input
class CreatePermissionInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.input
class AssignPermissionToRoleInput:
    role_id: strawberry.ID
    permission_id: strawberry.ID


@strawberry.input
class AssignRoleInput:
    company_user_id: strawberry.ID
    role_id: strawberry.ID



#  Account, Concept, AccountConcept, Transaction

@strawberry.enum
class AccountType(Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"
    WALLET = "WALLET"
    OTHER = "OTHER"


@strawberry.enum
class ConceptType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@strawberry.enum
class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@strawberry.type
class Account:
    id: strawberry.ID
    company: Company
    account_type: AccountType
    name: str
    bank_name: Optional[str]
    account_number: Optional[str]
    clabe: Optional[str]
    card_last_digits: Optional[str]
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time

    @strawberry.field
    def company_id(self) -> strawberry.ID:
        return self.company.id


@strawberry.type
class Concept:
    id: strawberry.ID
    company_id: strawberry.ID
    concept_type: ConceptType
    name: str
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time


@strawberry.type
class AccountConcept:
    id: strawberry.ID
    is_active: bool
    created_at: Time
    account: Account
    concept: Concept

    @strawberry.field
    def account_id(self) -> strawberry.ID:
        return self.account.id

    @strawberry.field
    def concept_id(self) -> strawberry.ID:
        return self.concept.id


@strawberry.type
class Transaction:
    id: strawberry.ID
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: Time
    captured_at: Time
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time
    account: Account
    concept: Concept
    captured_by_user: User

    @strawberry.field
    def account_id(self) -> strawberry.ID:
        return self.account.id

    @strawberry.field
    def concept_id(self) -> strawberry.ID:
        return self.concept.id

    @strawberry.field
    def captured_by(self) -> strawberry.ID:
        return self.captured_by_user.id


@strawberry.input
class CreateAccountInput:
    company_id: strawberry.ID
    account_type: AccountType
    name: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    clabe: Optional[str] = None
    card_last_digits: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None


@strawberry.input
class CreateConceptInput:
    company_id: strawberry.ID
    concept_type: ConceptType
    name: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None


@strawberry.input
class AssignConceptToAccountInput:
    account_id: strawberry.ID
    concept_id: strawberry.ID


@strawberry.input
class CreateTransactionInput:
    account_id: strawberry.ID
    concept_id: strawberry.ID
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: Optional[Time] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None



#  datos

sessions: dict[str, str] = {}

INITIAL_ROLES = [
    ("ADMINISTRADOR", "Administrador", "El administrador principal de la empresa"),
    ("CONTADOR", "Contador", "Quien arma cuentas y conceptos"),
    ("CAPTURISTA", "Capturista", "Quien registra movimientos"),
    ("CONSULTA", "Consulta", "Quien solo lee"),
]

INITIAL_PERMISSIONS = [
    ("company.users.read", "Ver membresías", "Ver las membresías de la empresa"),
    ("company.users.write", "Administrar usuarios", "Crear usuarios y desactivar membresías"),
    ("accounts.read", "Consultar cuentas", "Consultar cuentas"),
    ("accounts.write", "Crear cuentas", "Crear cuentas"),
    ("concepts.read", "Consultar conceptos", "Consultar conceptos"),
    ("concepts.write", "Administrar conceptos", "Crear conceptos y asignarlos a una cuenta"),
    ("transactions.read", "Consultar movimientos", "Consultar movimientos"),
    ("transactions.write", "Registrar movimientos", "Registrar un ingreso o un egreso"),
    ("roles.read", "Ver roles", "Ver roles y la matriz de permisos"),
    ("roles.write", "Administrar roles",
     "Asignar o quitar permisos de un rol, y asignar un rol a una membresía"),
]

INITIAL_MATRIX = {
    "ADMINISTRADOR": [code for code, _, _ in INITIAL_PERMISSIONS],
    "CONTADOR": [
        "company.users.read", "accounts.read", "accounts.write", "concepts.read",
        "concepts.write", "transactions.read", "transactions.write", "roles.read",
    ],
    "CAPTURISTA": [
        "accounts.read", "concepts.read", "transactions.read", "transactions.write",
    ],
    "CONSULTA": [
        "company.users.read", "accounts.read", "concepts.read", "transactions.read",
    ],
}


def find_role_by_code(db, code: str) -> Optional[RoleModel]:
    return db.query(RoleModel).filter(RoleModel.code == code).first()


def find_permission_by_code(db, code: str) -> Optional[PermissionModel]:
    return db.query(PermissionModel).filter(PermissionModel.code == code).first()


def seed_access_catalog() -> None:
    with SessionLocal() as db:
        if db.query(RoleModel).count() == 0:
            db.add_all([
                RoleModel(code=code, name=name, description=description, is_active=True)
                for code, name, description in INITIAL_ROLES
            ])
        if db.query(PermissionModel).count() == 0:
            db.add_all([
                PermissionModel(code=code, name=name, description=description, is_active=True)
                for code, name, description in INITIAL_PERMISSIONS
            ])
        db.flush()
        for role_code, permission_codes in INITIAL_MATRIX.items():
            role = find_role_by_code(db, role_code)
            if role is None or db.query(RolePermissionModel).filter(
                RolePermissionModel.role_id == role.id
            ).count() > 0:
                continue
            for permission_code in permission_codes:
                permission = find_permission_by_code(db, permission_code)
                if permission is not None:
                    db.add(RolePermissionModel(
                        role_id=role.id, permission_id=permission.id, is_active=True,
                    ))
        db.commit()


def active_role_assignment(db, company_user_id: str) -> Optional[CompanyUserRoleModel]:
    return (
        db.query(CompanyUserRoleModel)
        .filter(
            CompanyUserRoleModel.company_user_id == company_user_id,
            CompanyUserRoleModel.is_active.is_(True),
        )
        .first()
    )


def set_role(db, cu: CompanyUserModel, role: RoleModel) -> CompanyUserRoleModel:
    db.query(CompanyUserRoleModel).filter(
        CompanyUserRoleModel.company_user_id == cu.id,
        CompanyUserRoleModel.is_active.is_(True),
    ).update({CompanyUserRoleModel.is_active: False})
    assignment = CompanyUserRoleModel(company_user=cu, role=role, is_active=True)
    db.add(assignment)
    db.flush()
    return assignment


def exigir_permiso(db, company_user_id: str, codigo: str, company_id: str) -> CompanyUserModel:
    cu = db.get(CompanyUserModel, str(company_user_id))
    if cu is None or not cu.is_active or not cu.user.is_active:
        raise PermissionError("La membresía del actor no existe o no está activa.")
    if cu.company_id != company_id:
        raise PermissionError("La membresía del actor no pertenece a esta empresa.")

    asignacion = active_role_assignment(db, cu.id)
    if asignacion is None:
        raise PermissionError("La membresía no tiene un rol activo")
    if not asignacion.role.is_active:
        raise PermissionError(f"El rol {asignacion.role.code} está desactivado")

    permitido = (
        db.query(RolePermissionModel)
        .join(PermissionModel)
        .filter(
            RolePermissionModel.role_id == asignacion.role_id,
            RolePermissionModel.is_active.is_(True),
            PermissionModel.code == codigo,
            PermissionModel.is_active.is_(True),
        )
        .first()
    )
    if permitido is None:
        raise PermissionError(f"El rol no tiene el permiso {codigo}")
    return cu


def to_company(m: CompanyModel) -> Company:
    return Company(
        id=m.id, name=m.name, legal_name=m.legal_name, tax_id=m.tax_id, email=m.email,
        phone=m.phone, is_active=m.is_active, created_at=m.created_at, updated_at=m.updated_at,
    )


def to_user(m: UserModel) -> User:
    return User(
        id=m.id, name=m.name, email=m.email, hashed_password=m.hashed_password,
        email_verified=m.email_verified, is_active=m.is_active,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def to_role(m: RoleModel) -> Role:
    return Role(id=str(m.id), code=m.code, name=m.name,
                description=m.description, is_active=m.is_active)


def to_permission(m: PermissionModel) -> Permission:
    return Permission(id=str(m.id), code=m.code, name=m.name,
                      description=m.description, is_active=m.is_active)


def to_company_user(db, m: CompanyUserModel) -> CompanyUser:
    assignment = active_role_assignment(db, m.id)
    return CompanyUser(
        id=m.id, is_admin=m.is_admin, is_active=m.is_active, joined_at=m.joined_at,
        company=to_company(m.company), user=to_user(m.user),
        role=to_role(assignment.role) if assignment else None,
    )


def to_role_permission(m: RolePermissionModel) -> RolePermission:
    return RolePermission(id=str(m.id), role=to_role(m.role),
                          permission=to_permission(m.permission), is_active=m.is_active)


def to_company_user_role(db, m: CompanyUserRoleModel) -> CompanyUserRole:
    return CompanyUserRole(id=str(m.id), company_user=to_company_user(db, m.company_user),
                           role=to_role(m.role), is_active=m.is_active)


def to_account(m: AccountModel) -> Account:
    return Account(
        id=m.id, company=to_company(m.company), account_type=AccountType(m.account_type),
        name=m.name, bank_name=m.bank_name, account_number=m.account_number, clabe=m.clabe,
        card_last_digits=m.card_last_digits, short_description=m.short_description,
        long_description=m.long_description, is_active=m.is_active,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def to_concept(m: ConceptModel) -> Concept:
    return Concept(
        id=m.id, company_id=m.company_id, concept_type=ConceptType(m.concept_type),
        name=m.name, short_description=m.short_description,
        long_description=m.long_description, is_active=m.is_active,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def to_account_concept(m: AccountConceptModel) -> AccountConcept:
    return AccountConcept(id=m.id, is_active=m.is_active, created_at=m.created_at,
                          account=to_account(m.account), concept=to_concept(m.concept))


def to_transaction(m: TransactionModel) -> Transaction:
    return Transaction(
        id=m.id, transaction_type=TransactionType(m.transaction_type), amount=m.amount,
        transaction_date=m.transaction_date, captured_at=m.captured_at,
        short_description=m.short_description, long_description=m.long_description,
        is_active=m.is_active, created_at=m.created_at, updated_at=m.updated_at,
        account=to_account(m.account), concept=to_concept(m.concept),
        captured_by_user=to_user(m.captured_by_user),
    )


def find_user_by_email(db, email: str) -> Optional[UserModel]:
    email = email.strip().lower()
    return db.query(UserModel).filter(UserModel.email == email).first()


def has_active_admin(db, company_id: str) -> bool:
    return db.query(CompanyUserModel).filter(
        CompanyUserModel.company_id == company_id,
        CompanyUserModel.is_admin.is_(True),
        CompanyUserModel.is_active.is_(True),
    ).first() is not None


def user_company_ids(db, user_id: str) -> set:
    rows = db.query(CompanyUserModel.company_id).filter(
        CompanyUserModel.user_id == user_id, CompanyUserModel.is_active.is_(True),
    )
    return {company_id for (company_id,) in rows}


def get_active_company(db, company_id: str) -> CompanyModel:
    company = db.get(CompanyModel, company_id)
    if company is None:
        raise Exception(f"No existe una empresa con id '{company_id}'.")
    if not company.is_active:
        raise Exception(f"La empresa '{company.name}' está inactiva.")
    return company


def create_user(db, name: str, email: str, password: str) -> UserModel:
    if not name.strip():
        raise Exception("El nombre del usuario es obligatorio.")
    if not valid_email(email):
        raise Exception(f"El correo '{email}' no tiene un formato válido.")
    if len(password) < 8:
        raise Exception("La contraseña debe tener al menos 8 caracteres.")
    if find_user_by_email(db, email):
        raise Exception(f"El correo '{email}' ya está registrado.")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = UserModel(
        id=new_id(), name=name.strip(), email=email.strip().lower(),
        hashed_password=hashed, email_verified=False, is_active=True,
        created_at=now(), updated_at=now(),
    )
    db.add(user)
    return user


def current_user(db, info: strawberry.Info) -> UserModel:
    request = info.context.get("request") if isinstance(info.context, dict) else None
    auth = request.headers.get("authorization") if request else None
    token = auth.split(" ", 1)[1] if auth and auth.lower().startswith("bearer ") else None
    user_id = sessions.get(token) if token else None
    user = db.get(UserModel, user_id) if user_id else None
    if not user or not user.is_active:
        raise Exception(
            "No autenticado: mandá el header Authorization: Bearer <token> "
            "con el token que te dio login."
        )
    return user


Base.metadata.create_all(bind=engine)
seed_access_catalog()



# Query

@strawberry.type
class Query:
    @strawberry.field
    def companies(self, active_only: Optional[bool] = None) -> list[Company]:
        with SessionLocal() as db:
            q = db.query(CompanyModel)
            if active_only:
                q = q.filter(CompanyModel.is_active.is_(True))
            return [to_company(c) for c in q.order_by(CompanyModel.created_at)]

    @strawberry.field
    def company(self, id: strawberry.ID) -> Optional[Company]:
        with SessionLocal() as db:
            c = db.get(CompanyModel, str(id))
            return to_company(c) if c else None

    @strawberry.field
    def company_users(
        self, company_id: strawberry.ID, actor_company_user_id: strawberry.ID,
    ) -> list[CompanyUser]:
        with SessionLocal() as db:
            if db.get(CompanyModel, str(company_id)) is None:
                raise Exception(f"No existe una empresa con id '{company_id}'.")
            exigir_permiso(db, actor_company_user_id, "company.users.read", str(company_id))
            rows = db.query(CompanyUserModel).filter(
                CompanyUserModel.company_id == str(company_id)
            ).order_by(CompanyUserModel.joined_at)
            return [to_company_user(db, cu) for cu in rows]

    @strawberry.field
    def accounts(
        self, company_id: strawberry.ID, actor_company_user_id: strawberry.ID,
        account_type: Optional[AccountType] = None,
        active_only: Optional[bool] = None,
    ) -> list[Account]:
        with SessionLocal() as db:
            exigir_permiso(db, actor_company_user_id, "accounts.read", str(company_id))
            q = db.query(AccountModel).filter(AccountModel.company_id == str(company_id))
            if account_type is not None:
                q = q.filter(AccountModel.account_type == account_type.value)
            if active_only:
                q = q.filter(AccountModel.is_active.is_(True))
            return [to_account(a) for a in q.order_by(AccountModel.created_at)]

    @strawberry.field
    def concepts(
        self, company_id: strawberry.ID, actor_company_user_id: strawberry.ID,
        concept_type: Optional[ConceptType] = None,
        active_only: Optional[bool] = None,
    ) -> list[Concept]:
        with SessionLocal() as db:
            exigir_permiso(db, actor_company_user_id, "concepts.read", str(company_id))
            q = db.query(ConceptModel).filter(ConceptModel.company_id == str(company_id))
            if concept_type is not None:
                q = q.filter(ConceptModel.concept_type == concept_type.value)
            if active_only:
                q = q.filter(ConceptModel.is_active.is_(True))
            return [to_concept(c) for c in q.order_by(ConceptModel.created_at)]

    @strawberry.field
    def account_concepts(
        self, account_id: strawberry.ID, actor_company_user_id: strawberry.ID,
    ) -> list[AccountConcept]:
        with SessionLocal() as db:
            account = db.get(AccountModel, str(account_id))
            if account is None:
                raise Exception(f"No existe una cuenta con id '{account_id}'.")
            exigir_permiso(db, actor_company_user_id, "concepts.read", account.company_id)
            rows = db.query(AccountConceptModel).filter(
                AccountConceptModel.account_id == account.id
            ).order_by(AccountConceptModel.created_at)
            return [to_account_concept(ac) for ac in rows]

    @strawberry.field
    def transactions(
        self, actor_company_user_id: strawberry.ID,
        account_id: Optional[strawberry.ID] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: Optional[int] = None, offset: Optional[int] = None,
    ) -> list[Transaction]:
        with SessionLocal() as db:
            actor = db.get(CompanyUserModel, str(actor_company_user_id))
            if actor is None:
                raise PermissionError("La membresía del actor no existe o no está activa.")
            exigir_permiso(db, actor.id, "transactions.read", actor.company_id)
            q = db.query(TransactionModel).join(AccountModel).filter(
                AccountModel.company_id == actor.company_id
            )
            if account_id is not None:
                q = q.filter(TransactionModel.account_id == str(account_id))
            if transaction_type is not None:
                q = q.filter(TransactionModel.transaction_type == transaction_type.value)
            q = q.order_by(TransactionModel.created_at, TransactionModel.id)
            if offset:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(limit)
            return [to_transaction(t) for t in q]

    @strawberry.field
    def roles(self, active_only: Optional[bool] = None) -> list[Role]:
        with SessionLocal() as db:
            q = db.query(RoleModel)
            if active_only:
                q = q.filter(RoleModel.is_active.is_(True))
            return [to_role(r) for r in q.order_by(RoleModel.id)]

    @strawberry.field
    def role(self, id: strawberry.ID) -> Optional[Role]:
        with SessionLocal() as db:
            r = db.get(RoleModel, int_id(id))
            return to_role(r) if r else None

    @strawberry.field
    def permissions(self, active_only: Optional[bool] = None) -> list[Permission]:
        with SessionLocal() as db:
            q = db.query(PermissionModel)
            if active_only:
                q = q.filter(PermissionModel.is_active.is_(True))
            return [to_permission(p) for p in q.order_by(PermissionModel.id)]

    @strawberry.field
    def role_permissions(self, role_id: strawberry.ID) -> list[RolePermission]:
        with SessionLocal() as db:
            if db.get(RoleModel, int_id(role_id)) is None:
                raise Exception(f"No existe un rol con id '{role_id}'.")
            rows = db.query(RolePermissionModel).filter(
                RolePermissionModel.role_id == int_id(role_id),
                RolePermissionModel.is_active.is_(True),
            ).order_by(RolePermissionModel.permission_id)
            return [to_role_permission(rp) for rp in rows]



# Mutation

@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_company(self, input: CreateCompanyInput) -> Company:
        if not input.name.strip():
            raise Exception("El nombre de la empresa es obligatorio.")
        if input.email and not valid_email(input.email):
            raise Exception(f"El correo '{input.email}' no tiene un formato válido.")
        with SessionLocal() as db:
            company = CompanyModel(
                id=new_id(), name=input.name.strip(), legal_name=input.legal_name,
                tax_id=input.tax_id, email=input.email, phone=input.phone,
                is_active=True, created_at=now(), updated_at=now(),
            )
            db.add(company)
            db.commit()
            return to_company(company)

    @strawberry.mutation
    def update_company(self, input: UpdateCompanyInput) -> Company:
        with SessionLocal() as db:
            company = db.get(CompanyModel, str(input.id))
            if company is None:
                raise Exception(f"No existe una empresa con id '{input.id}'.")
            if input.name is not None:
                company.name = input.name.strip()
            if input.legal_name is not None:
                company.legal_name = input.legal_name
            if input.tax_id is not None:
                company.tax_id = input.tax_id
            if input.email is not None:
                if input.email and not valid_email(input.email):
                    raise Exception(f"El correo '{input.email}' no tiene un formato válido.")
                company.email = input.email
            if input.phone is not None:
                company.phone = input.phone
            if input.is_active is not None:
                company.is_active = input.is_active
            company.updated_at = now()
            db.commit()
            return to_company(company)

    @strawberry.mutation
    def deactivate_company(self, id: strawberry.ID) -> Company:
        with SessionLocal() as db:
            company = db.get(CompanyModel, str(id))
            if company is None:
                raise Exception(f"No existe una empresa con id '{id}'.")
            company.is_active = False
            company.updated_at = now()
            db.commit()
            return to_company(company)

    @strawberry.mutation
    def login(self, input: LoginInput) -> AuthPayload:
        with SessionLocal() as db:
            user = find_user_by_email(db, input.email)
            if not user or not user.is_active or not bcrypt.checkpw(
                input.password.encode(), user.hashed_password.encode()
            ):
                raise Exception("Correo o contraseña incorrectos.")
            token = secrets.token_urlsafe(32)
            sessions[token] = user.id
            return AuthPayload(
                token=token, token_type="Bearer",
                user=AuthUser(id=user.id, name=user.name, email=user.email),
            )

    @strawberry.mutation
    def create_company_admin(self, input: CreateCompanyAdminInput) -> CompanyUser:
        with SessionLocal() as db:
            company = get_active_company(db, str(input.company_id))
            if has_active_admin(db, company.id):
                raise Exception("La empresa ya tiene un administrador principal activo.")
            admin_role = find_role_by_code(db, "ADMINISTRADOR")
            if admin_role is None or not admin_role.is_active:
                raise Exception("El rol ADMINISTRADOR no existe o está desactivado.")
            user = create_user(db, input.name, input.email, input.password)
            cu = CompanyUserModel(id=new_id(), is_admin=True, is_active=True, joined_at=now(),
                                  company=company, user=user)
            db.add(cu)
            set_role(db, cu, admin_role)
            db.commit()
            return to_company_user(db, cu)

    @strawberry.mutation
    def create_company_user(
        self, input: CreateCompanyUserInput, actor_company_user_id: strawberry.ID,
    ) -> CompanyUser:
        with SessionLocal() as db:
            company = get_active_company(db, str(input.company_id))
            exigir_permiso(db, actor_company_user_id, "company.users.write", company.id)
            default_role = find_role_by_code(db, "CONSULTA")
            if default_role is None or not default_role.is_active:
                raise Exception("El rol CONSULTA no existe o está desactivado.")
            user = create_user(db, input.name, input.email, input.password)
            cu = CompanyUserModel(id=new_id(), is_admin=False, is_active=True, joined_at=now(),
                                  company=company, user=user)
            db.add(cu)
            set_role(db, cu, default_role)
            db.commit()
            return to_company_user(db, cu)

    @strawberry.mutation
    def deactivate_company_user(
        self, id: strawberry.ID, actor_company_user_id: strawberry.ID,
    ) -> CompanyUser:
        with SessionLocal() as db:
            cu = db.get(CompanyUserModel, str(id))
            if cu is None:
                raise Exception(f"No existe una relación empresa-usuario con id '{id}'.")
            exigir_permiso(db, actor_company_user_id, "company.users.write", cu.company_id)
            cu.is_active = False
            db.commit()
            return to_company_user(db, cu)


    @strawberry.mutation
    def create_account(
        self, input: CreateAccountInput, actor_company_user_id: strawberry.ID,
    ) -> Account:
        with SessionLocal() as db:
            company = db.get(CompanyModel, str(input.company_id))
            if company is None:
                raise Exception(f"No existe una empresa con id '{input.company_id}'.")
            exigir_permiso(db, actor_company_user_id, "accounts.write", company.id)
            if not input.name.strip():
                raise Exception("El nombre de la cuenta es obligatorio.")
            if any(
                a.name.strip().lower() == input.name.strip().lower()
                for a in db.query(AccountModel).filter(AccountModel.company_id == company.id)
            ):
                raise Exception(f"La empresa ya tiene una cuenta llamada '{input.name}'.")

            account = AccountModel(
                id=new_id(), company=company, account_type=input.account_type.value,
                name=input.name.strip(), bank_name=input.bank_name,
                account_number=input.account_number, clabe=input.clabe,
                card_last_digits=input.card_last_digits,
                short_description=input.short_description, long_description=input.long_description,
                is_active=True, created_at=now(), updated_at=now(),
            )
            db.add(account)
            db.commit()
            return to_account(account)

    @strawberry.mutation
    def create_concept(
        self, input: CreateConceptInput, actor_company_user_id: strawberry.ID,
    ) -> Concept:
        with SessionLocal() as db:
            company = db.get(CompanyModel, str(input.company_id))
            if company is None:
                raise Exception(f"No existe una empresa con id '{input.company_id}'.")
            exigir_permiso(db, actor_company_user_id, "concepts.write", company.id)
            if not input.name.strip():
                raise Exception("El nombre del concepto es obligatorio.")
            if any(
                c.name.strip().lower() == input.name.strip().lower()
                for c in db.query(ConceptModel).filter(
                    ConceptModel.company_id == company.id,
                    ConceptModel.concept_type == input.concept_type.value,
                )
            ):
                raise Exception(
                    f"La empresa ya tiene un concepto de {input.concept_type.value} "
                    f"llamado '{input.name}'."
                )

            concept = ConceptModel(
                id=new_id(), company_id=company.id, concept_type=input.concept_type.value,
                name=input.name.strip(), short_description=input.short_description,
                long_description=input.long_description, is_active=True,
                created_at=now(), updated_at=now(),
            )
            db.add(concept)
            db.commit()
            return to_concept(concept)

    @strawberry.mutation
    def assign_concept_to_account(
        self, input: AssignConceptToAccountInput, actor_company_user_id: strawberry.ID,
    ) -> AccountConcept:
        with SessionLocal() as db:
            account = db.get(AccountModel, str(input.account_id))
            if account is None:
                raise Exception(f"No existe una cuenta con id '{input.account_id}'.")
            concept = db.get(ConceptModel, str(input.concept_id))
            if concept is None:
                raise Exception(f"No existe un concepto con id '{input.concept_id}'.")
            if concept.company_id != account.company_id:
                raise Exception("La cuenta y el concepto deben pertenecer a la misma empresa.")
            exigir_permiso(db, actor_company_user_id, "concepts.write", account.company_id)
            if db.query(AccountConceptModel).filter(
                AccountConceptModel.account_id == account.id,
                AccountConceptModel.concept_id == concept.id,
                AccountConceptModel.is_active.is_(True),
            ).first():
                raise Exception("Ese concepto ya está asignado a esa cuenta.")

            ac = AccountConceptModel(id=new_id(), account=account, concept=concept,
                                     is_active=True, created_at=now())
            db.add(ac)
            db.commit()
            return to_account_concept(ac)

    @strawberry.mutation
    def remove_concept_from_account(
        self, account_id: strawberry.ID, concept_id: strawberry.ID,
        actor_company_user_id: strawberry.ID,
    ) -> bool:
        with SessionLocal() as db:
            account = db.get(AccountModel, str(account_id))
            if account is None:
                raise Exception(f"No existe una cuenta con id '{account_id}'.")
            exigir_permiso(db, actor_company_user_id, "concepts.write", account.company_id)
            ac = db.query(AccountConceptModel).filter(
                AccountConceptModel.account_id == str(account_id),
                AccountConceptModel.concept_id == str(concept_id),
                AccountConceptModel.is_active.is_(True),
            ).first()
            if ac is None:
                raise Exception("No existe una relación activa entre esa cuenta y ese concepto.")
            ac.is_active = False
            db.commit()
            return True

    @strawberry.mutation
    def create_transaction(
        self, info: strawberry.Info, input: CreateTransactionInput,
        actor_company_user_id: strawberry.ID,
    ) -> Transaction:
        with SessionLocal() as db:
            user = current_user(db, info)
            actor = db.get(CompanyUserModel, str(actor_company_user_id))
            if actor is None or actor.user_id != user.id:
                raise PermissionError(
                    "La membresía del actor no corresponde al usuario autenticado."
                )

            account = db.get(AccountModel, str(input.account_id))
            if account is None:
                raise Exception(f"No existe una cuenta con id '{input.account_id}'.")
            concept = db.get(ConceptModel, str(input.concept_id))
            if concept is None:
                raise Exception(f"No existe un concepto con id '{input.concept_id}'.")
            if input.amount <= 0:
                raise Exception("El monto debe ser mayor que cero.")

            allowed = db.query(AccountConceptModel).filter(
                AccountConceptModel.account_id == account.id,
                AccountConceptModel.concept_id == concept.id,
                AccountConceptModel.is_active.is_(True),
            ).first()
            if not allowed:
                raise Exception("Ese concepto no está permitido para esa cuenta.")
            if concept.company_id != account.company_id:
                raise Exception("La cuenta y el concepto deben pertenecer a la misma empresa.")
            if account.company_id not in user_company_ids(db, user.id):
                raise Exception("El usuario no pertenece a la empresa de esa cuenta.")
            if input.transaction_type.value != concept.concept_type:
                raise Exception(
                    f"El tipo de movimiento debe coincidir con el tipo de concepto "
                    f"({concept.concept_type})."
                )
            exigir_permiso(db, actor.id, "transactions.write", account.company_id)

            transaction = TransactionModel(
                id=new_id(), account=account, concept=concept,
                transaction_type=input.transaction_type.value, amount=input.amount,
                transaction_date=to_utc(input.transaction_date) if input.transaction_date else now(),
                captured_at=now(), captured_by_user=user,
                short_description=input.short_description,
                long_description=input.long_description, is_active=True,
                created_at=now(), updated_at=now(),
            )
            db.add(transaction)
            db.commit()
            return to_transaction(transaction)

    @strawberry.mutation
    def delete_transaction(
        self, id: strawberry.ID, actor_company_user_id: strawberry.ID,
    ) -> Transaction:
        with SessionLocal() as db:
            t = db.get(TransactionModel, str(id))
            if t is None:
                raise Exception(f"No existe un movimiento con id '{id}'.")
            exigir_permiso(db, actor_company_user_id, "transactions.write", t.account.company_id)
            t.is_active = False
            t.updated_at = now()
            db.commit()
            return to_transaction(t)


    @strawberry.mutation
    def create_role(self, input: CreateRoleInput) -> Role:
        code = input.code.strip().upper()
        if not code or not input.name.strip():
            raise Exception("El código y el nombre del rol son obligatorios.")
        with SessionLocal() as db:
            if find_role_by_code(db, code):
                raise Exception(f"Ya existe un rol con código '{code}'.")
            role = RoleModel(code=code, name=input.name.strip(),
                             description=input.description, is_active=True)
            db.add(role)
            db.commit()
            return to_role(role)

    @strawberry.mutation
    def deactivate_role(self, id: strawberry.ID) -> Role:
        with SessionLocal() as db:
            role = db.get(RoleModel, int_id(id))
            if role is None:
                raise Exception(f"No existe un rol con id '{id}'.")
            role.is_active = False
            db.commit()
            return to_role(role)

    @strawberry.mutation
    def create_permission(self, input: CreatePermissionInput) -> Permission:
        code = input.code.strip().lower()
        if not code or not input.name.strip():
            raise Exception("El código y el nombre del permiso son obligatorios.")
        with SessionLocal() as db:
            if find_permission_by_code(db, code):
                raise Exception(f"Ya existe un permiso con código '{code}'.")
            permission = PermissionModel(code=code, name=input.name.strip(),
                                         description=input.description, is_active=True)
            db.add(permission)
            db.commit()
            return to_permission(permission)

    @strawberry.mutation
    def assign_permission_to_role(
        self, input: AssignPermissionToRoleInput, actor_company_user_id: strawberry.ID,
    ) -> RolePermission:
        with SessionLocal() as db:
            actor = db.get(CompanyUserModel, str(actor_company_user_id))
            if actor is None:
                raise PermissionError("La membresía del actor no existe o no está activa.")
            exigir_permiso(db, actor.id, "roles.write", actor.company_id)
            role = db.get(RoleModel, int_id(input.role_id))
            if role is None or not role.is_active:
                raise Exception(f"No existe un rol activo con id '{input.role_id}'.")
            permission = db.get(PermissionModel, int_id(input.permission_id))
            if permission is None or not permission.is_active:
                raise Exception(f"No existe un permiso activo con id '{input.permission_id}'.")
            if db.query(RolePermissionModel).filter(
                RolePermissionModel.role_id == role.id,
                RolePermissionModel.permission_id == permission.id,
                RolePermissionModel.is_active.is_(True),
            ).first():
                raise Exception(f"El rol {role.code} ya tiene el permiso {permission.code}.")
            rp = RolePermissionModel(role=role, permission=permission, is_active=True)
            db.add(rp)
            db.commit()
            return to_role_permission(rp)

    @strawberry.mutation
    def remove_permission_from_role(
        self, role_id: strawberry.ID, permission_id: strawberry.ID,
        actor_company_user_id: strawberry.ID,
    ) -> bool:
        with SessionLocal() as db:
            actor = db.get(CompanyUserModel, str(actor_company_user_id))
            if actor is None:
                raise PermissionError("La membresía del actor no existe o no está activa.")
            exigir_permiso(db, actor.id, "roles.write", actor.company_id)
            rp = db.query(RolePermissionModel).filter(
                RolePermissionModel.role_id == int_id(role_id),
                RolePermissionModel.permission_id == int_id(permission_id),
                RolePermissionModel.is_active.is_(True),
            ).first()
            if rp is None:
                raise Exception("No existe una relación activa entre ese rol y ese permiso.")
            rp.is_active = False
            db.commit()
            return True

    @strawberry.mutation
    def assign_role(
        self, input: AssignRoleInput, actor_company_user_id: strawberry.ID,
    ) -> CompanyUserRole:
        with SessionLocal() as db:
            cu = db.get(CompanyUserModel, str(input.company_user_id))
            if cu is None or not cu.is_active:
                raise Exception(
                    f"No existe una membresía activa con id '{input.company_user_id}'."
                )
            exigir_permiso(db, actor_company_user_id, "roles.write", cu.company_id)
            role = db.get(RoleModel, int_id(input.role_id))
            if role is None or not role.is_active:
                raise Exception(f"No existe un rol activo con id '{input.role_id}'.")
            current = active_role_assignment(db, cu.id)
            if current and current.role_id == role.id:
                raise Exception(f"La membresía ya tiene el rol {role.code}.")
            assignment = set_role(db, cu, role)
            db.commit()
            return to_company_user_role(db, assignment)


schema = strawberry.Schema(query=Query, mutation=Mutation)
