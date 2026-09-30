from typing import List, Dict, Any, Optional
import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.course import Course, CourseSource, Enrollment, EnrollmentStatus
from app.models.competency import Competency
from app.schemas.recommendation import RecommendedCourseItem, PathwayResponse
from app.services.gap_analyzer import CompetencyGapAnalyzer

# MoSPI Operational Division Keywords
DIVISION_KEYWORDS: Dict[str, List[str]] = {
    "FOD": ["survey", "sampling", "field", "cpi", "listing", "nss", "data collection", "capi", "respondent", "fieldwork", "price collection"],
    "NAD": ["national accounts", "gdp", "gva", "macroeconomic", "sna", "sut", "supply and use", "consumption", "capital formation"],
    "ESD": ["price", "cpi", "index", "inflation", "iip", "asi", "annual survey of industries", "economic census", "wholesale"],
    "SDRD": ["sampling", "survey design", "plfs", "labour", "questionnaire", "statistical theory", "estimation", "sae", "variance"],
    "DPD": ["data processing", "python", "sql", "database", "cleaning", "tabulation", "automation", "microdata", "wrangling"],
    "SSD": ["sdg", "sustainable development", "social", "gender", "environment", "indicators", "esg", "localization"],
    "DIID": ["ai", "ml", "gis", "mapping", "machine learning", "cloud", "dashboard", "portal", "geospatial", "remote sensing"],
    "NSSTA": ["training", "capacity building", "methodology", "workshop", "residential", "faculty", "pedagogy"],
}

class HybridRecommender:
    @staticmethod
    def get_personalized_pathway(
        db: Session,
        user: User,
        source_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        max_duration: Optional[float] = None,
    ) -> PathwayResponse:
        """
        Executes hybrid recommendation matching combining:
        1. Rule-based urgent competency gap indexing (WUS > 0)
        2. Keyword and semantic profile alignment (division, cadre, experience)
        3. Dual-track segregation: Track A (iGOT Karmayogi) & Track B (NSSTA TPAC)
        4. Personalized rationale explanation generation
        """
        # 1. Run gap analysis for the officer
        gap_analysis = CompetencyGapAnalyzer.analyze_gaps(db, user)
        gaps_map = {item.code: item for item in gap_analysis.all_competencies}
        comp_id_map = {item.competency_id: item for item in gap_analysis.all_competencies}

        # Query all active courses
        courses_query = db.query(Course).filter(Course.is_active == True)
        if source_filter:
            courses_query = courses_query.filter(Course.source == source_filter)
        courses = courses_query.all()

        # Query existing user enrollments
        user_enrollments = {
            e.course_id: e
            for e in db.query(Enrollment).filter(Enrollment.user_id == user.id).all()
        }

        # Query competency details for metadata
        all_comps_db = {c.code: c for c in db.query(Competency).all()}

        recommended_items: List[RecommendedCourseItem] = []

        # Division keywords for profile matching
        div_keywords = DIVISION_KEYWORDS.get(user.division, ["statistics", "data", "mospi"])

        for course in courses:
            if max_duration and course.duration_hours > max_duration:
                continue

            target_comps: List[str] = course.target_competencies or []
            if not target_comps:
                continue

            # Check if domain filter applies
            if domain_filter:
                match_domain = False
                for tc in target_comps:
                    c_obj = all_comps_db.get(tc)
                    if c_obj and c_obj.domain.lower() == domain_filter.lower():
                        match_domain = True
                        break
                if not match_domain:
                    continue

            # 2. Rule-Based Gap Matching Logic
            best_gap_item = None
            max_urgency = -1.0
            primary_code = target_comps[0]

            for tc in target_comps:
                gap_item = gaps_map.get(tc)
                if gap_item:
                    urgency = gap_item.urgency_score
                    if urgency > max_urgency:
                        max_urgency = urgency
                        best_gap_item = gap_item
                        primary_code = tc

            c_obj = all_comps_db.get(primary_code)
            bridged_gap_name = c_obj.name if c_obj else primary_code
            bridged_gap_urgency = best_gap_item.urgency_score if best_gap_item else 0.0
            officer_current_level = best_gap_item.current_level if best_gap_item else 1
            officer_required_level = best_gap_item.required_level if best_gap_item else 2

            # Calculate base rule score
            if best_gap_item and best_gap_item.gap > 0:
                # Urgent gap: scale with urgency score
                rule_score = min(0.95, 0.45 + (best_gap_item.urgency_score / 12.0) * 0.45)
            elif best_gap_item and best_gap_item.current_level >= best_gap_item.required_level:
                # Skill enrichment/mastery
                rule_score = 0.35
            else:
                # Elective / emerging technology
                rule_score = 0.30

            # Level stepping factor (Next level step gets highest affinity)
            level_diff = course.target_level - officer_current_level
            if level_diff == 1:
                rule_score += 0.08 # Ideal incremental progression
            elif level_diff == 0:
                rule_score += 0.04 # Reinforcement of current level
            elif level_diff > 2:
                rule_score -= 0.10 # Too advanced for immediate jump

            # 3. Profile & Semantic Keyword Alignment
            content_text = f"{course.title} {course.description}".lower()
            keyword_hits = sum(1 for kw in div_keywords if re.search(r'\b' + re.escape(kw) + r'\b', content_text))
            div_similarity = min(0.30, keyword_hits * 0.08)

            # Cadre and Designation alignment
            cadre_bonus = 0.0
            if user.designation.lower() in content_text or user.cadre.lower() in content_text:
                cadre_bonus = 0.15
            elif "officer" in content_text or "director" in content_text or "personnel" in content_text:
                cadre_bonus = 0.08

            # Course quality / rating factor
            rating_factor = (course.rating / 5.0) * 0.08

            profile_similarity = min(1.0, div_similarity + cadre_bonus + rating_factor + 0.35)

            # Composite Relevance Percentage (0.0 to 100.0%)
            composite_score = round(((rule_score * 0.65) + (profile_similarity * 0.35)) * 100, 1)
            composite_score = max(35.0, min(99.0, composite_score))

            # 4. Generate Contextual Personalized Rationale
            rationale_parts = []
            if best_gap_item and best_gap_item.gap > 0:
                if best_gap_item.status == "CRITICAL_GAP":
                    rationale_parts.append(
                        f"Priority Action: Directly addresses a critical competency deficiency in {bridged_gap_name} ({primary_code}), where your current Level {officer_current_level} falls below the required Level {officer_required_level} for {user.designation}."
                    )
                else:
                    rationale_parts.append(
                        f"Recommended for bridging your moderate gap in {bridged_gap_name} ({primary_code}) towards achieving Level {course.target_level} mastery."
                    )
            else:
                rationale_parts.append(
                    f"Selected for cadre enrichment in {bridged_gap_name} ({primary_code}) to enhance your statistical domain leadership."
                )

            if keyword_hits > 0:
                rationale_parts.append(
                    f"Aligns directly with your core operational workflows in the {user.division} division."
                )

            if course.source == CourseSource.IGOT_KARMAYOGI.value:
                rationale_parts.append(
                    f"Delivered on iGOT Karmayogi as an interactive {course.duration_hours}h self-paced digital module with instant competency evaluation."
                )
            elif course.source == CourseSource.NSSTA_TPAC.value:
                loc = course.location or "NSSTA Greater Noida"
                rationale_parts.append(
                    f"Approved by the Training Programme Approval Committee (TPAC) for in-depth residential capacity building ({course.duration_hours}h) at {loc}."
                )

            full_rationale = " ".join(rationale_parts)

            # Check enrollment status
            enr = user_enrollments.get(course.id)
            if enr:
                enr_status = enr.status
                prog = enr.progress_percentage
                enrolled_at = enr.enrolled_at
                completed_at = enr.completed_at
            else:
                enr_status = "RECOMMENDED"
                prog = 0
                enrolled_at = None
                completed_at = None

            recommended_items.append(
                RecommendedCourseItem(
                    course_id=course.id,
                    external_id=course.external_id,
                    source=course.source,
                    title=course.title,
                    description=course.description,
                    provider=course.provider,
                    duration_hours=course.duration_hours,
                    delivery_mode=course.delivery_mode,
                    location=course.location,
                    rating=course.rating,
                    thumbnail_url=course.thumbnail_url,
                    course_url=course.course_url,
                    batch_start_date=course.batch_start_date,
                    batch_capacity=course.batch_capacity,
                    target_competencies=target_comps,
                    target_level=course.target_level,
                    relevance_score=composite_score,
                    bridged_gap_code=primary_code,
                    bridged_gap_name=bridged_gap_name,
                    bridged_gap_urgency=bridged_gap_urgency,
                    recommendation_rationale=full_rationale,
                    enrollment_status=enr_status,
                    progress_percentage=prog,
                    enrolled_at=enrolled_at,
                    completed_at=completed_at,
                )
            )

        # Sort all recommendations by relevance score descending
        recommended_items.sort(key=lambda x: x.relevance_score, reverse=True)

        # Segregate into Track A and Track B
        track_a = [c for c in recommended_items if c.source == CourseSource.IGOT_KARMAYOGI.value]
        track_b = [c for c in recommended_items if c.source == CourseSource.NSSTA_TPAC.value]

        critical_gaps_count = sum(1 for g in gap_analysis.all_competencies if g.gap >= 2 or g.urgency_score >= 2.0)

        return PathwayResponse(
            officer_name=user.full_name,
            designation=user.designation,
            division=user.division,
            cadre=user.cadre,
            overall_readiness_percentage=gap_analysis.overall_readiness_percentage,
            critical_gaps_count=critical_gaps_count,
            track_a_igot_courses=track_a,
            track_b_tpac_courses=track_b,
            all_recommendations=recommended_items,
        )
