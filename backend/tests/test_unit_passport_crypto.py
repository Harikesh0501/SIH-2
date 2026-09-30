import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.competency import UserCompetency
from app.services.passport_service import PassportService

def test_sha256_cryptographic_hashing():
    """
    Verifies that SHA-256 hash generation produces standard 64-character hex strings
    and is strictly deterministic.
    """
    payload = "MOSPI:4:STAT-SURV:3:2026-09-28:SALT"
    hash1 = PassportService.generate_sha256_hash(payload)
    hash2 = PassportService.generate_sha256_hash(payload)

    assert len(hash1) == 64
    assert hash1 == hash2

    # Different payload must produce distinct hash
    hash3 = PassportService.generate_sha256_hash(payload + "_altered")
    assert hash1 != hash3

def test_qr_code_base64_generation():
    """
    Verifies that generate_qr_code_base64 outputs a valid data URI containing base64 PNG data.
    """
    url = "http://localhost:3000/verify/MOSPI-CRED-STAT-SURV-L3-0004"
    qr_uri = PassportService.generate_qr_code_base64(url)

    assert qr_uri.startswith("data:image/png;base64,")
    assert len(qr_uri) > 100

def test_privacy_email_masking(db_session: Session):
    """
    Verifies that public credential audit masks officer email for privacy protection.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    assert user is not None

    # Sync credentials
    creds = PassportService.sync_user_credentials(db_session, user)
    assert len(creds) > 0

    first_cred = creds[0]
    result = PassportService.verify_credential(db_session, first_cred.credential_code)

    assert result["valid"] is True
    assert result["status"] == "OFFICIALLY_VERIFIED"
    assert "recipient" in result

    masked = result["recipient"]["masked_email"]
    # Email jso.sharma@mospi.gov.in should be masked as j***a@mospi.gov.in
    assert "@mospi.gov.in" in masked
    assert "jso.sharma" not in masked
    assert "***" in masked

def test_tamper_evident_credential_verification(db_session: Session):
    """
    Verifies that valid credentials verify successfully, while invalid or altered
    codes/hashes return status INVALID_OR_NOT_FOUND.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    creds = PassportService.sync_user_credentials(db_session, user)
    cred = creds[0]

    # 1. Audit with valid credential code
    res_code = PassportService.verify_credential(db_session, cred.credential_code)
    assert res_code["valid"] is True
    assert res_code["credential"]["level_awarded"] == cred.level_awarded

    # 2. Audit with valid cryptographic hash
    res_hash = PassportService.verify_credential(db_session, cred.qr_code_hash)
    assert res_hash["valid"] is True

    # 3. Audit with forged or non-existent code
    res_invalid = PassportService.verify_credential(db_session, "FORGED-CODE-9999")
    assert res_invalid["valid"] is False
    assert res_invalid["status"] == "INVALID_OR_NOT_FOUND"

def test_mastery_badge_evaluation(db_session: Session):
    """
    Verifies dynamic awarding of MoSPI domain badges based on competency levels.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    user_comps = db_session.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()

    badges = PassportService.evaluate_mastery_badges(db_session, user, user_comps)
    assert len(badges) > 0

    badge_codes = [b["code"] for b in badges]
    # JSO Pooja Sharma has STAT-SURV L3 in conftest -> qualifies for STAT-SURV-SPEC (NSS Specialist, Gold)
    assert "STAT-SURV-SPEC" in badge_codes

    surv_badge = next(b for b in badges if b["code"] == "STAT-SURV-SPEC")
    assert surv_badge["tier"] == "GOLD"
    assert surv_badge["category"] == "STATISTICAL"
