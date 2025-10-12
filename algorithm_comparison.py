from models import db, User, Session, Assignment, Unavailability, UserRole, SkillLevel, FacilitatorSkill
from datetime import datetime, timedelta
import json
import math
import random
import numpy as np
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class AlgorithmType(Enum):
    THRESHOLD_HYBRID = "threshold_hybrid"

@dataclass
class AlgorithmWeights:
    """Configuration for algorithm weights"""
    availability: float = 1.0
    skill_match: float = 0.8
    skill_level: float = 0.6
    preference: float = 0.4
    experience: float = 0.3
    workload_balance: float = 0.5

@dataclass
class FacilitatorMetrics:
    """Metrics for evaluating facilitator suitability"""
    availability: float  # 0 or 1 (boolean)
    skill_match_ratio: float  # 0-1
    avg_skill_level: float  # 0-1 (normalized)
    preference_score: float  # 0-1
    experience_score: float  # 0-1
    workload_score: float  # 0-1 (inverse of current workload)

class AdvancedSchedulingEngine:
    """Advanced scheduling engine with multiple algorithm implementations"""
    
    def __init__(self, weights: AlgorithmWeights = None):
        self.weights = weights or AlgorithmWeights()
        self.epsilon = 1e-6  # Small value to avoid log(0)
        
        # Algorithm-specific weight adjustments
        self.algorithm_weights = {
            AlgorithmType.THRESHOLD_HYBRID: AlgorithmWeights(
                availability=0.30, skill_match=0.25, skill_level=0.20, 
                preference=0.15, experience=0.05, workload_balance=0.05
            )
        }
    
    def calculate_facilitator_metrics(self, facilitator: User, session: Session) -> FacilitatorMetrics:
        """Calculate comprehensive metrics for a facilitator-session pair"""
        
        # Availability check (boolean: 0 or 1)
        availability = 1.0 if self._is_facilitator_available(facilitator, session) else 0.0
        
        # Skill match ratio
        if session.required_skills:
            # Handle comma-separated string format
            required_skills = [skill.strip() for skill in session.required_skills.split(',')]
        else:
            required_skills = []
        facilitator_skills = self._get_facilitator_skills(facilitator)
        
        if required_skills:
            matched_skills = len(set(required_skills) & set(facilitator_skills.keys()))
            skill_match_ratio = matched_skills / len(required_skills)
        else:
            skill_match_ratio = 1.0  # No specific requirements
        
        # Average skill level (normalized)
        if facilitator_skills and required_skills:
            relevant_skills = [facilitator_skills.get(skill, 0) for skill in required_skills]
            avg_skill_level = sum(relevant_skills) / len(relevant_skills) if relevant_skills else 0.0
        else:
            avg_skill_level = 0.5  # Default moderate level
        
        # Preference score (simplified)
        preferences = json.loads(facilitator.preferences) if facilitator.preferences else {}
        preference_score = self._calculate_preference_score(preferences, session)
        
        # Experience score (based on past assignments)
        experience_score = self._calculate_experience_score(facilitator)
        
        # Workload balance score
        workload_score = self._calculate_workload_score(facilitator, session)
        
        return FacilitatorMetrics(
            availability=availability,
            skill_match_ratio=skill_match_ratio,
            avg_skill_level=avg_skill_level,
            preference_score=preference_score,
            experience_score=experience_score,
            workload_score=workload_score
        )
    

    
    def threshold_hybrid_algorithm(self, metrics: FacilitatorMetrics) -> float:
        """Algorithm 4: Threshold-Hybrid (Sum + business floor)"""
        if metrics.availability == 0:
            return 0.0
        
        weights = self.algorithm_weights[AlgorithmType.THRESHOLD_HYBRID]
        
        # Define more reasonable thresholds for practical use
        thresholds = {
            'skill_match': 0.3,  # 降低要求：至少30%技能匹配
            'skill_level': 0.4,  # 降低要求：平均技能水平40%以上
            'preference': 0.2,
            'experience': 0.2,
            'workload': 0.2
        }
        
        # Check if facilitator meets minimum thresholds
        if (metrics.skill_match_ratio < thresholds['skill_match'] or
            metrics.avg_skill_level < thresholds['skill_level']):
            return 0.0  # Reject if critical thresholds not met
        
        # Calculate weighted score for those who pass thresholds
        score = (
            weights.availability * metrics.availability +
            weights.skill_match * metrics.skill_match_ratio +
            weights.skill_level * metrics.avg_skill_level +
            weights.preference * metrics.preference_score +
            weights.experience * metrics.experience_score +
            weights.workload_balance * metrics.workload_score
        )
        return score
    
    def calculate_score(self, facilitator: User, session: Session, algorithm: AlgorithmType) -> float:
        """Calculate score using specified algorithm"""
        metrics = self.calculate_facilitator_metrics(facilitator, session)
        
        if algorithm == AlgorithmType.THRESHOLD_HYBRID:
            return self.threshold_hybrid_algorithm(metrics)
        else:
            raise ValueError(f"Unknown algorithm type: {algorithm}")
    
    def find_best_facilitator(self, session: Session, algorithm: AlgorithmType) -> User:
        """Find the best facilitator for a session using the specified algorithm"""
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        available_facilitators = []
        
        # Apply algorithm-specific availability filtering
        for facilitator in facilitators:
            if self._is_facilitator_available_for_algorithm(facilitator, session, algorithm):
                score = self.calculate_score(facilitator, session, algorithm)
                if score > 0:  # Only consider facilitators with positive scores
                    available_facilitators.append((facilitator, score))
        
        if not available_facilitators:
            return None
        
        # Threshold hybrid selection strategy
        if algorithm == AlgorithmType.THRESHOLD_HYBRID:
            # Strict threshold: only top 25% qualify, then select by skill match priority
            available_facilitators.sort(key=lambda x: x[1], reverse=True)
            top_quarter = available_facilitators[:max(1, len(available_facilitators)//4)]
            # Among top quarter, prioritize skill match over raw score
            best_facilitator, best_score = max(top_quarter, key=lambda x: (
                self.calculate_facilitator_metrics(x[0], session).skill_match_ratio,
                self.calculate_facilitator_metrics(x[0], session).avg_skill_level,
                x[1]
            ))
        else:
            raise ValueError(f"Unknown algorithm type: {algorithm}")
        
        return best_facilitator
    
    def find_best_facilitator_with_constraints(self, session: Session, algorithm: AlgorithmType, 
                                             assigned_facilitators: set, facilitator_schedules: dict) -> User:
        """Find the best facilitator considering existing assignments and time conflicts"""
        facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
        available_facilitators = []
        
        # Apply algorithm-specific availability filtering with constraint checking
        for facilitator in facilitators:
            # Skip if facilitator is already assigned (only for most strict algorithm)
            if algorithm == AlgorithmType.THRESHOLD_HYBRID:
                if facilitator.id in assigned_facilitators:
                    continue
            
            # Check for time conflicts
            if facilitator.id in facilitator_schedules:
                has_conflict = False
                for existing_session in facilitator_schedules[facilitator.id]:
                    if self._sessions_overlap(session, existing_session):
                        has_conflict = True
                        break
                if has_conflict:
                    continue
            
            # Apply algorithm-specific filtering
            if self._is_facilitator_available_for_algorithm(facilitator, session, algorithm):
                score = self.calculate_score(facilitator, session, algorithm)
                if score > 0:  # Only consider facilitators with positive scores
                    available_facilitators.append((facilitator, score))
        
        if not available_facilitators:
            return None
        
        # Apply threshold hybrid selection strategy
        if algorithm == AlgorithmType.THRESHOLD_HYBRID:
            # Strict threshold: only top 25% qualify, then select by skill match priority
            available_facilitators.sort(key=lambda x: x[1], reverse=True)
            top_quarter = available_facilitators[:max(1, len(available_facilitators)//4)]
            # Among top quarter, prioritize skill match over raw score
            best_facilitator, best_score = max(top_quarter, key=lambda x: (
                self.calculate_facilitator_metrics(x[0], session).skill_match_ratio,
                self.calculate_facilitator_metrics(x[0], session).avg_skill_level,
                x[1]
            ))
        else:
            raise ValueError(f"Unknown algorithm type: {algorithm}")
        
        return best_facilitator
    
    def _sessions_overlap(self, session1: Session, existing_session: dict) -> bool:
        """Check if two sessions have time overlap"""
        start1, end1 = session1.start_time, session1.end_time
        start2 = existing_session['start_time']
        end2 = existing_session['end_time']
        
        # Sessions overlap if one starts before the other ends
        return not (end1 <= start2 or end2 <= start1)
    
    def generate_schedule(self, algorithm: AlgorithmType, randomize: bool = False) -> Dict[str, Any]:
        """Generate schedule using specified algorithm"""
        try:
            sessions = Session.query.all()
            facilitators = User.query.filter_by(role=UserRole.FACILITATOR).all()
            
            if randomize:
                random.shuffle(sessions)
                random.shuffle(facilitators)
            
            assignments = []
            conflicts = []
            algorithm_scores = []
            assigned_facilitators = set()  # Track assigned facilitators
            facilitator_schedules = {}  # Track facilitator time commitments
            
            for session in sessions:
                best_facilitator = self.find_best_facilitator_with_constraints(
                    session, algorithm, assigned_facilitators, facilitator_schedules
                )
                
                if best_facilitator:
                    score = self.calculate_score(best_facilitator, session, algorithm)
                    if score > 0:
                        assignments.append({
                            'session_id': session.id,
                            'facilitator_id': best_facilitator.id,
                            'facilitator_name': f"{best_facilitator.first_name} {best_facilitator.last_name}",
                            'session_info': f"{session.module.unit.unit_code} - {session.module.module_name}",
                            'score': score,
                            'algorithm': algorithm.value
                        })
                        algorithm_scores.append(score)
                        
                        # Track assignment to prevent double-booking
                        assigned_facilitators.add(best_facilitator.id)
                        if best_facilitator.id not in facilitator_schedules:
                            facilitator_schedules[best_facilitator.id] = []
                        facilitator_schedules[best_facilitator.id].append({
                            'start_time': session.start_time,
                            'end_time': session.end_time,
                            'session_id': session.id
                        })
                    else:
                        conflicts.append({
                            'session_id': session.id,
                            'session_name': f"{session.module.unit.unit_code} - {session.module.module_name}",
                            'reason': 'No suitable facilitator found'
                        })
                else:
                    conflicts.append({
                        'session_id': session.id,
                        'session_name': f"{session.module.unit.unit_code} - {session.module.module_name}",
                        'reason': 'No available facilitator meets algorithm criteria'
                    })
            
            return {
                'success': True,
                'algorithm': algorithm.value,
                'assignments': assignments,
                'conflicts': conflicts,
                'total_sessions': len(sessions),
                'assigned_sessions': len(assignments),
                'assignment_rate': len(assignments) / len(sessions) if sessions else 0,
                'avg_score': np.mean(algorithm_scores) if algorithm_scores else 0,
                'score_std': np.std(algorithm_scores) if algorithm_scores else 0,
                'min_score': min(algorithm_scores) if algorithm_scores else 0,
                'max_score': max(algorithm_scores) if algorithm_scores else 0
            }
        
        except Exception as e:
            return {
                'success': False,
                'algorithm': algorithm.value,
                'error': str(e)
            }
    
    # Helper methods
    def _is_facilitator_available(self, facilitator: User, session: Session) -> bool:
        """Check availability by ensuring no overlapping Unavailability on the session date."""
        session_date = session.start_time.date()
        session_start_time = session.start_time.time()
        session_end_time = session.end_time.time()

        # Find any unavailability on that date for this facilitator
        blocks = (
            Unavailability.query
            .filter(
                Unavailability.user_id == facilitator.id,
                Unavailability.date == session_date,
            )
            .all()
        )

        # If any full-day block exists -> unavailable
        for b in blocks:
            if b.is_full_day:
                return False

        # If any time-overlap block exists -> unavailable
        for b in blocks:
            if b.start_time is None or b.end_time is None:
                continue
            # overlap if block.start < session_end and block.end > session_start
            if b.start_time < session_end_time and b.end_time > session_start_time:
                return False

        # Otherwise available
        return True
    
    def _is_facilitator_available_for_algorithm(self, facilitator: User, session: Session, algorithm: AlgorithmType) -> bool:
        """Algorithm-specific availability checking with different strictness levels"""
        # Base availability check
        if not self._is_facilitator_available(facilitator, session):
            return False
        
        # Algorithm-specific additional filtering
        if algorithm == AlgorithmType.THRESHOLD_HYBRID:
            # Reasonable requirements - require moderate skill match and level
            metrics = self.calculate_facilitator_metrics(facilitator, session)
            return (metrics.skill_match_ratio >= 0.3 and 
                   metrics.avg_skill_level >= 0.4)
        else:
            raise ValueError(f"Unknown algorithm type: {algorithm}")
    
    def _get_facilitator_skills(self, facilitator: User) -> Dict[str, float]:
        """Get facilitator skills with normalized levels"""
        skills = {}
        facilitator_skills = FacilitatorSkill.query.filter_by(facilitator_id=facilitator.id).all()
        
        skill_level_map = {
            SkillLevel.INTERESTED: 0.25,
            SkillLevel.HAVE_RUN_BEFORE: 0.9,
            SkillLevel.PROFICIENT: 0.75,
            SkillLevel.LEADER: 1.0,
            SkillLevel.UNINTERESTED: 0.0
        }
        
        for skill in facilitator_skills:
            skills[skill.module.module_name] = skill_level_map.get(skill.skill_level, 0.0)
        
        return skills
    
    def _calculate_preference_score(self, preferences: Dict, session: Session) -> float:
        """Calculate preference score based on session characteristics"""
        # Simplified preference calculation
        score = 0.5  # Default neutral preference
        
        # Time preference
        hour = session.start_time.hour
        if preferences.get('preferred_time') == 'morning' and 8 <= hour < 12:
            score += 0.3
        elif preferences.get('preferred_time') == 'afternoon' and 12 <= hour < 17:
            score += 0.3
        elif preferences.get('preferred_time') == 'evening' and 17 <= hour < 21:
            score += 0.3
        
        # Session type preference
        if session.session_type in preferences.get('preferred_types', []):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_experience_score(self, facilitator: User) -> float:
        """Calculate experience score based on past assignments"""
        assignment_count = Assignment.query.filter_by(facilitator_id=facilitator.id).count()
        # Normalize to 0-1 scale (assuming max 50 assignments for full experience)
        return min(assignment_count / 50.0, 1.0)
    
    def _calculate_workload_score(self, facilitator: User, session: Session) -> float:
        """Calculate workload balance score (higher score for less loaded facilitators)"""
        # Count current assignments in the same week
        week_start = session.start_time - timedelta(days=session.start_time.weekday())
        week_end = week_start + timedelta(days=7)
        
        current_workload = Assignment.query.filter_by(facilitator_id=facilitator.id).join(Session).filter(
            Session.start_time >= week_start,
            Session.start_time < week_end
        ).count()
        
        # Inverse workload score (less workload = higher score)
        max_workload = 10  # Assume max 10 sessions per week
        return max(0, (max_workload - current_workload) / max_workload)