from sqlalchemy import Column,Integer,String,Float,DateTime
from sqlalchemy.sql import func
from .db import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer,primary_key=True,index=True)
    pair = Column(String,index=True)
    signal = Column(String) 
    predicted_price = Column(Float)
    actual_price= Column(Float,nullable = True)
    timestamp = Column(DateTime(timezone=True),server_default=func.now())

    def as_dict(self):
        return {
            "id": self.id,
            "pair": self.pair,
            "signal": self.signal,
            "predicted_price": self.predicted_price,
            "actual_price": self.actual_price,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

#Redundant Table 
class Accuracy(Base):
    __tablename__ = "accuracy"

    id = Column(Integer,primary_key=True,index=True)
    pair = Column(String, index=True)
    total = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
