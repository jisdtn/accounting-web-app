# from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float
# from sqlalchemy.orm import relationship
#
# from .database import Base
#
#
# class Category(Base):
#     __tablename__ = "categories"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String, unique=True, index=True)
#     currency = Column(String, index=True)
#
#     balances = relationship("Balance", back_populates="category")
#
#
# class Balance(Base):
#     __tablename__ = "balances"
#
#     cat_id = Column(Integer, ForeignKey("categories.id"))
#     date = Column(Date, index=True)
#     value = Column(Integer)
#     rate = Column(Float)
#
#     category = relationship("Category", back_populates="balances")
