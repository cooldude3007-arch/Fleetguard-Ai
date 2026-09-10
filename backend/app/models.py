from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Date,
    Boolean,
    ForeignKey
)

from .database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vin = Column(String, primary_key=True)
    model = Column(String, nullable=False)
    region = Column(String, nullable=False)
    registration_date = Column(Date, nullable=False)
    total_km_driven = Column(Integer, nullable=False)


class Part(Base):
    __tablename__ = "parts"

    part_code = Column(String, primary_key=True)
    part_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    design_life_km = Column(Integer, nullable=False)


class Failure(Base):
    __tablename__ = "failures"

    job_card_id = Column(String, primary_key=True)
    vin = Column(String, ForeignKey("vehicles.vin"), nullable=False)
    part_code = Column(
        String,
        ForeignKey("parts.part_code"),
        nullable=False
    )
    failure_date = Column(Date, nullable=False)
    odometer_at_failure = Column(Integer, nullable=False)
    replaced = Column(Boolean, nullable=False)


class Telematics(Base):
    __tablename__ = "telematics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    vin = Column(String, ForeignKey("vehicles.vin"), nullable=False)
    week_start_date = Column(Date, nullable=False)

    coolant_temp_variance = Column(Float, nullable=False)
    oil_pressure_dips = Column(Integer, nullable=False)
    battery_voltage_sag = Column(Float, nullable=False)
    dtc_recurrence_rate = Column(Float, nullable=False)
    harsh_braking_frequency = Column(Float, nullable=False)
    overload_duty_share = Column(Float, nullable=False)
    high_rpm_dwell_time = Column(Float, nullable=False)
    short_trip_ratio = Column(Float, nullable=False)
    idle_time_pct = Column(Float, nullable=False)


class RuleConfig(Base):
    __tablename__ = "rule_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    part_code = Column(
        String,
        ForeignKey("parts.part_code"),
        nullable=False
    )

    signal = Column(String, nullable=False)
    correlation_weight = Column(Float, nullable=False)
    included = Column(Boolean, nullable=False)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    vin = Column(
        String,
        ForeignKey("vehicles.vin"),
        nullable=False
    )

    part_code = Column(
        String,
        ForeignKey("parts.part_code"),
        nullable=False
    )

    failure_probability = Column(Float, nullable=False)
    risk_tier = Column(String, nullable=False)

    estimated_window = Column(String, nullable=True)

    rul_km = Column(Float, nullable=True)
    rul_days = Column(Float, nullable=True)

    computed_date = Column(Date, nullable=False)