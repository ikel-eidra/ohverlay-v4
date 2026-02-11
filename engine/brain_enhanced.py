"""
Enhanced Behavioral AI for Super-Realistic Betta Fish Movement.

This module extends the base BehavioralReactor with advanced features:
- Fin kinematics simulation (pectoral, caudal, dorsal fin movement)
- Body undulation physics
- Breathing gill movements
- Advanced mood expression through body language
- Memory-based behavior (learns preferred spots)
- Time-of-day behavior patterns
- Social awareness (responds to cursor proximity)

All within 16GB RAM / CPU constraints.
"""

import numpy as np
import math
import time
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class FinState:
    """Simulated fin kinematics for realistic animation."""
    # Pectoral fins (left/right)
    pectoral_left_angle: float = 0.0
    pectoral_right_angle: float = 0.0
    pectoral_left_phase: float = 0.0
    pectoral_right_phase: float = 0.0
    
    # Caudal (tail) fin
    tail_angle: float = 0.0
    tail_amplitude: float = 0.0
    tail_frequency: float = 8.0  # Hz
    
    # Dorsal fin (top)
    dorsal_erection: float = 0.5  # 0 = flat, 1 = fully erect
    dorsal_wave: float = 0.0
    
    # Anal fin (bottom)
    anal_spread: float = 0.3
    
    def update(self, dt: float, speed: float, accel: float, mood: float):
        """Update fin kinematics based on movement."""
        # Pectoral fins flutter when moving, still when resting
        base_freq = 4.0 + speed * 0.05
        self.pectoral_left_phase += dt * base_freq * (1 + speed * 0.01)
        self.pectoral_right_phase += dt * base_freq * 1.1  # Slight asymmetry
        
        self.pectoral_left_angle = math.sin(self.pectoral_left_phase) * (0.3 + speed * 0.002)
        self.pectoral_right_angle = math.sin(self.pectoral_right_phase) * (0.3 + speed * 0.002)
        
        # Tail amplitude based on speed and acceleration
        target_amp = 0.2 + min(speed / 300, 0.6) + min(accel / 200, 0.3)
        self.tail_amplitude += (target_amp - self.tail_amplitude) * dt * 5
        
        # Tail oscillation
        self.tail_angle = math.sin(time.time() * self.tail_frequency * 2 * math.pi) * self.tail_amplitude
        
        # Dorsal fin erects when alert/flaring
        if mood < 40:  # Flaring/stressed
            target_dorsal = 1.0
        elif mood > 80:  # Happy/exploring
            target_dorsal = 0.7
        else:
            target_dorsal = 0.5
        self.dorsal_erection += (target_dorsal - self.dorsal_erection) * dt * 2
        
        # Anal fin spreads during display
        target_anal = 0.3 + (1 - mood / 100) * 0.5
        self.anal_spread += (target_anal - self.anal_spread) * dt * 1.5


@dataclass
class BodyKinematics:
    """Body shape and posture simulation."""
    # Spine curvature for undulation
    spine_angles: List[float] = None  # 5 segments from head to tail
    
    # Gill movement (breathing)
    gill_openness: float = 0.3
    gill_phase: float = 0.0
    
    # Eye direction
    eye_offset: float = 0.0  # -1 to 1 (looking left/right relative to body)
    
    # Body tilt (for turning/banking)
    roll_angle: float = 0.0  # Banking into turns
    pitch_angle: float = 0.0  # Nose up/down
    
    def __post_init__(self):
        if self.spine_angles is None:
            self.spine_angles = [0.0] * 5
    
    def update(self, dt: float, velocity: np.ndarray, facing_angle: float, 
               turn_rate: float, speed: float):
        """Update body kinematics based on movement."""
        # Breathing rate increases with activity
        breath_rate = 0.5 + speed * 0.005
        self.gill_phase += dt * breath_rate
        self.gill_openness = 0.2 + math.sin(self.gill_phase) * 0.15 + speed * 0.001
        
        # Eye tracking (look slightly toward movement direction)
        target_eye = np.clip(turn_rate * 2, -0.5, 0.5)
        self.eye_offset += (target_eye - self.eye_offset) * dt * 3
        
        # Banking into turns (roll)
        target_roll = -turn_rate * 0.5  # Bank opposite to turn
        self.roll_angle += (target_roll - self.roll_angle) * dt * 4
        
        # Pitch based on vertical velocity
        if speed > 1:
            vy_norm = velocity[1] / speed
            target_pitch = vy_norm * 0.3  # Nose up/down
        else:
            target_pitch = 0
        self.pitch_angle += (target_pitch - self.pitch_angle) * dt * 3
        
        # Spine undulation (wave propagates head to tail)
        undulation_freq = 6.0 + speed * 0.02
        for i, _ in enumerate(self.spine_angles):
            phase_offset = i * 0.5
            base_undulation = math.sin(time.time() * undulation_freq + phase_offset) * 0.1
            # Add speed-based undulation
            speed_undulation = (speed / 400) * math.sin(time.time() * undulation_freq * 2 + phase_offset) * 0.2
            self.spine_angles[i] = base_undulation + speed_undulation


class MemorySystem:
    """
    Simple spatial memory system.
    Fish remembers preferred resting spots, feeding locations, etc.
    """
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        # Memory entries: (position, type, timestamp, rating)
        self.memories: deque = deque(maxlen=capacity)
        self.favorite_rest_spots: List[Tuple[float, float]] = []
        
    def add_memory(self, pos: np.ndarray, mem_type: str, rating: float = 0.5):
        """Add a spatial memory."""
        entry = {
            'pos': pos.copy(),
            'type': mem_type,  # 'rest', 'feed', 'explore', 'avoid'
            'timestamp': time.time(),
            'rating': rating  # 0-1, higher = more preferred
        }
        self.memories.append(entry)
        
        # Update favorite spots
        if mem_type == 'rest' and rating > 0.7:
            self.favorite_rest_spots.append((pos[0], pos[1]))
            if len(self.favorite_rest_spots) > 5:
                self.favorite_rest_spots.pop(0)
    
    def get_preferred_rest_spot(self, current_pos: np.ndarray, 
                                 bounds: List[float]) -> Optional[np.ndarray]:
        """Get a remembered good resting spot."""
        if not self.favorite_rest_spots:
            return None
        
        # Choose based on recency + distance
        candidates = []
        for spot in self.favorite_rest_spots:
            dist = np.linalg.norm(np.array(spot) - current_pos)
            # Prefer closer spots but also explore occasionally
            score = 1.0 / (1 + dist * 0.01) + random.uniform(0, 0.3)
            candidates.append((score, spot))
        
        candidates.sort(reverse=True)
        best = candidates[0][1]
        return np.array(best)
    
    def get_recent_feed_area(self) -> Optional[np.ndarray]:
        """Get location of recent feeding."""
        recent_feeds = [
            m for m in self.memories 
            if m['type'] == 'feed' and time.time() - m['timestamp'] < 3600
        ]
        if recent_feeds:
            return recent_feeds[-1]['pos']
        return None


class EnvironmentalAwareness:
    """
    Awareness of environment and interactions.
    - Cursor proximity detection
    - Activity level tracking
    - Time-of-day behavior modulation
    """
    def __init__(self):
        self.cursor_pos = np.array([0.0, 0.0])
        self.cursor_velocity = np.array([0.0, 0.0])
        self.cursor_nearby_time = 0.0
        self.last_cursor_update = time.time()
        
        # Activity tracking
        self.activity_level = 0.5  # 0-1, how active the user is
        self.activity_history = deque(maxlen=60)  # 1 minute of samples
        
        # Time of day
        self.nocturnal_preference = 0.3  # 0 = diurnal, 1 = nocturnal
        
    def update_cursor(self, pos: Tuple[float, float]):
        """Update cursor tracking."""
        now = time.time()
        dt = now - self.last_cursor_update
        if dt > 0:
            new_pos = np.array(pos)
            self.cursor_velocity = (new_pos - self.cursor_pos) / dt
            self.cursor_pos = new_pos
        self.last_cursor_update = now
        
    def is_cursor_near(self, fish_pos: np.ndarray, threshold: float = 150.0) -> bool:
        """Check if cursor is near fish."""
        dist = np.linalg.norm(self.cursor_pos - fish_pos)
        return dist < threshold
    
    def get_cursor_interest_factor(self, fish_pos: np.ndarray) -> float:
        """
        How interested should the fish be in the cursor?
        Returns 0-1 factor.
        """
        dist = np.linalg.norm(self.cursor_pos - fish_pos)
        if dist > 300:
            return 0.0
        
        # Closer = more interesting
        proximity = 1.0 - dist / 300
        
        # Moving cursor is more interesting
        cursor_speed = np.linalg.norm(self.cursor_velocity)
        movement_factor = min(cursor_speed / 500, 1.0)
        
        return proximity * 0.5 + movement_factor * 0.5
    
    def update_activity(self):
        """Update user activity tracking."""
        cursor_speed = np.linalg.norm(self.cursor_velocity)
        self.activity_history.append(cursor_speed)
        
        # Calculate activity level
        if len(self.activity_history) > 10:
            avg_activity = sum(self.activity_history) / len(self.activity_history)
            self.activity_level = min(avg_activity / 200, 1.0)
    
    def get_time_of_day_factor(self) -> float:
        """
        Get behavior modifier based on time of day.
        Returns 0-1 where 0 = sleepy time, 1 = active time
        """
        hour = time.localtime().tm_hour
        
        # Betta fish are generally active during day
        if 6 <= hour < 10:  # Morning
            return 0.3 + self.nocturnal_preference * 0.3
        elif 10 <= hour < 14:  # Midday
            return 0.8 - self.nocturnal_preference * 0.2
        elif 14 <= hour < 18:  # Afternoon
            return 0.9 - self.nocturnal_preference * 0.3
        elif 18 <= hour < 22:  # Evening
            return 0.6
        else:  # Night
            return 0.2 + self.nocturnal_preference * 0.6


class EnhancedBettaBrain:
    """
    Enhanced brain for super-realistic Betta fish.
    Combines all enhancement systems while staying within CPU/RAM budget.
    """
    
    def __init__(self, base_brain):
        """
        Wraps a base BehavioralReactor with enhanced features.
        
        Args:
            base_brain: The BehavioralReactor instance to enhance
        """
        self.base = base_brain
        
        # Enhancement systems
        self.fins = FinState()
        self.body = BodyKinematics()
        self.memory = MemorySystem()
        self.env = EnvironmentalAwareness()
        
        # Enhanced state tracking
        self.last_enhancement_update = time.time()
        self.previous_velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])
        
        # Personality traits (randomized for variety)
        self.curiosity = random.uniform(0.6, 1.0)
        self.shyness = random.uniform(0.1, 0.4)
        self.playfulness = random.uniform(0.4, 0.9)
        
        # Turn rate tracking for body kinematics
        self.previous_facing = 0.0
        self.turn_rate = 0.0
        
    def update(self, cursor_pos: Optional[Tuple[float, float]] = None):
        """
        Update enhanced systems.
        Call this after base_brain.update()
        """
        now = time.time()
        dt = now - self.last_enhancement_update
        self.last_enhancement_update = now
        
        # Update base brain first
        self.base.update()
        
        # Calculate acceleration
        self.acceleration = (self.base.velocity - self.previous_velocity) / max(dt, 0.001)
        self.previous_velocity = self.base.velocity.copy()
        
        # Calculate turn rate
        self.turn_rate = self.base.facing_angle - self.previous_facing
        # Normalize turn rate
        while self.turn_rate > math.pi:
            self.turn_rate -= 2 * math.pi
        while self.turn_rate < -math.pi:
            self.turn_rate += 2 * math.pi
        self.turn_rate /= max(dt, 0.001)
        self.previous_facing = self.base.facing_angle
        
        speed = np.linalg.norm(self.base.velocity)
        accel_mag = np.linalg.norm(self.acceleration)
        
        # Update subsystems
        self.fins.update(dt, speed, accel_mag, self.base.mood)
        self.body.update(dt, self.base.velocity, self.base.facing_angle, 
                        self.turn_rate, speed)
        self.env.update_activity()
        
        if cursor_pos:
            self.env.update_cursor(cursor_pos)
        
        # Memory updates
        if self.base.state == "RESTING" and random.random() < 0.01:
            self.memory.add_memory(self.base.position, 'rest', rating=0.8)
        
    def get_enhanced_state(self) -> dict:
        """
        Get complete enhanced state for rendering.
        Includes all base state plus enhanced kinematics.
        """
        base_state = self.base.get_state()
        
        enhanced = {
            **base_state,
            # Fin kinematics
            'pectoral_left_angle': self.fins.pectoral_left_angle,
            'pectoral_right_angle': self.fins.pectoral_right_angle,
            'tail_angle': self.fins.tail_angle,
            'tail_amplitude': self.fins.tail_amplitude,
            'dorsal_erection': self.fins.dorsal_erection,
            'anal_spread': self.fins.anal_spread,
            
            # Body kinematics
            'spine_angles': self.body.spine_angles.copy(),
            'gill_openness': self.body.gill_openness,
            'eye_offset': self.body.eye_offset,
            'roll_angle': self.body.roll_angle,
            'pitch_angle': self.body.pitch_angle,
            
            # Environmental
            'cursor_nearby': self.env.is_cursor_near(self.base.position),
            'cursor_interest': self.env.get_cursor_interest_factor(self.base.position),
            'time_of_day_factor': self.env.get_time_of_day_factor(),
            'activity_level': self.env.activity_level,
            
            # Personality
            'curiosity': self.curiosity,
            'shyness': self.shyness,
            'playfulness': self.playfulness,
            
            # Physics
            'acceleration': self.acceleration.tolist(),
            'turn_rate': self.turn_rate,
        }
        
        return enhanced
    
    def should_investigate_cursor(self) -> bool:
        """Decide if fish should swim toward cursor."""
        if self.base.state in ["FLARING", "RESTING"]:
            return False
        
        interest = self.env.get_cursor_interest_factor(self.base.position)
        
        # Modulate by personality
        if self.shyness > 0.7 and interest < 0.8:
            return False
        
        if self.curiosity > 0.8:
            interest *= 1.2
        
        return random.random() < interest * 0.1  # 10% chance at max interest
    
    def get_cursor_target(self) -> np.ndarray:
        """Get position near cursor to investigate."""
        # Approach cursor but keep some distance (shy fish keep more distance)
        offset_dist = 50 + self.shyness * 100
        angle = random.uniform(0, 2 * math.pi)
        offset = np.array([math.cos(angle), math.sin(angle)]) * offset_dist
        return self.env.cursor_pos + offset


# Convenience function to enhance any base brain
def enhance_brain(base_brain) -> EnhancedBettaBrain:
    """Wrap a base BehavioralReactor with enhanced systems."""
    return EnhancedBettaBrain(base_brain)
