# from datetime import date
# from pydantic import BaseModel
#
#
# class CategoryBase(BaseModel):
#     name: str
#     currency: str
#
#
# class CategoryCreate(CategoryBase):
#     pass
#
#
# class Category(CategoryBase):
#     id: int
#
#     class Config:
#         orm_mode = True
#
#
# class BalanceBase(BaseModel):
#     date: date
#     value: int
#     rate: int
#
#
# class BalanceCreate(BalanceBase):
#     pass
#
#
# class Balance(BalanceBase):
#     cat_id: int
#     categories: list[Category] = []
#
#     class Config:
#         orm_mode = True

