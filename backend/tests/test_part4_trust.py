import pytest
from datetime import datetime, timedelta
from app.trust.scorer import TrustScorer

@pytest.fixture
def scorer():
    return TrustScorer()

def test_https_scoring(scorer):
    # HTTPS should give points
    res = scorer.assess_trust("https://example.com", "example.com", "some text")
    assert res["trust_signals"]["https"] is True
    assert res["trust_score"] >= scorer.weights["https"]
    
    # HTTP should not
    res_http = scorer.assess_trust("http://example.com", "example.com", "some text")
    assert res_http["trust_signals"]["https"] is False
    assert res_http["trust_score"] < res["trust_score"]

def test_tld_scoring(scorer):
    # .edu should give points
    res = scorer.assess_trust("https://university.edu", "university.edu", "some text")
    assert res["trust_signals"]["tld_authority"] is True
    assert res["trust_score"] >= scorer.weights["tld_authority"]
    
    # .com should not
    res_com = scorer.assess_trust("https://example.com", "example.com", "some text")
    assert res_com["trust_signals"]["tld_authority"] is False

def test_citation_signal(scorer):
    # Should detect references at the end
    text = "Here is some content. " * 100 + "References: [1] Author, A. (2020)."
    res = scorer.assess_trust("https://example.com", "example.com", text)
    assert res["trust_signals"]["citation_quality"] > 0
    
    # Standard citations format
    text2 = "Some claim [1]. Another claim [2]."
    res2 = scorer.assess_trust("https://example.com", "example.com", text2)
    assert res2["trust_signals"]["citation_quality"] > 0

def test_freshness_signal(scorer):
    # Recent (within 30 days)
    recent_date = datetime.utcnow() - timedelta(days=5)
    res_recent = scorer.assess_trust("https://example.com", "example.com", "text", published_at=recent_date)
    assert res_recent["trust_signals"]["freshness"] == scorer.weights["freshness"]
    
    # Older (within 1 year)
    old_date = datetime.utcnow() - timedelta(days=200)
    res_old = scorer.assess_trust("https://example.com", "example.com", "text", published_at=old_date)
    assert res_old["trust_signals"]["freshness"] == scorer.weights["freshness"] * 0.5
    
    # Very old
    very_old_date = datetime.utcnow() - timedelta(days=500)
    res_very_old = scorer.assess_trust("https://example.com", "example.com", "text", published_at=very_old_date)
    assert res_very_old["trust_signals"]["freshness"] == 0

def test_trust_levels(scorer):
    # Test normalization and levels
    res = scorer.assess_trust("https://university.edu", "university.edu", "References [1]", published_at=datetime.utcnow())
    assert res["trust_score"] <= 100
    assert res["trust_level"] in ["High", "Medium", "Low"]
    
    if res["trust_score"] >= 80:
        assert res["trust_level"] == "High"
