import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gig import Gig, GigStatus


@pytest.mark.asyncio
async def test_create_gig(async_session: AsyncSession):
    gig = Gig(
        category="Programming & Tech",
        subcategory="Python",
        title_template="I will write a {task} python script",
        description_template="Custom python script for {task}",
        title="I will write python script",
        description="Custom python script",
        package_basic_price=10,
        package_basic_days=3,
        package_basic_revisions=2,
        package_basic_features=["Feature A"],
        package_standard_price=25,
        package_standard_days=2,
        package_standard_revisions=3,
        package_standard_features=["Feature A", "Feature B"],
        package_premium_price=50,
        package_premium_days=1,
        package_premium_revisions=5,
        package_premium_features=["Feature A", "Feature B", "Feature C"],
        extras_json=[],
        faq_json=[],
        requirements_json=[],
        image_urls="",
        tags="python, script",
        ab_variants_json={},
    )
    async_session.add(gig)
    await async_session.commit()
    assert gig.id is not None
    assert gig.status == GigStatus.DRAFT
    assert gig.category == "Programming & Tech"
    assert gig.title == "I will write python script"
