from typing import List
import pandas as pd
import json

from expense_analysis.tools import get_hash

class Correction:
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        return {**vars(self), "class": self.__class__.__name__}


class CategoryNameCorrection(Correction):
    CORRECTION_FIELD = "category_name"


class DateCorrection(Correction):
    CORRECTION_FIELD = "date"
    
class CorrectionFromLabel(Correction):
    TARGET_FIELD = "label"
    

class CategoryCorrectionWhereLabelContains(CategoryNameCorrection, CorrectionFromLabel):

    def __init__(self, contains: str, to_lower: bool, correct_value: str, comments: str | None = None) -> None:
        self.contains = contains
        self.to_lower = to_lower
        self.correct_value = correct_value
        self.comments = comments

    def apply(self, df: pd.DataFrame) -> None:
        if self.to_lower:
            index = df[self.TARGET_FIELD].fillna("").str.lower().str.contains(self.contains.lower())
        else:
            index = df[self.TARGET_FIELD].fillna("").str.contains(self.contains)
        df.loc[index, self.CORRECTION_FIELD] = self.correct_value


class CategoryCorrectionFromLoc(CategoryNameCorrection):

    def __init__(self, loc_id: int, correct_value: str, comments: str | None = None) -> None:
        self.loc_id = loc_id
        self.correct_value = correct_value
        self.comments = comments

    def apply(self, df: pd.DataFrame) -> None:
        df.loc[self.loc_id, self.CORRECTION_FIELD] = self.correct_value


class DateCorrectionFromLoc(DateCorrection):

    def __init__(self, loc_id: int, correct_value: str, comments: str | None = None) -> None:
        self.loc_id = loc_id
        self.correct_value = correct_value
        self.comments = comments

    def apply(self, df: pd.DataFrame) -> None:
        df.loc[self.loc_id, self.CORRECTION_FIELD] = self.correct_value
        

class RowDroppingFromLoc(Correction):

    def __init__(self, loc_id: int, comments: str | None = None) -> None:
        self.loc_id = loc_id
        self.comments = comments

    def apply(self, df: pd.DataFrame) -> None:
        df.drop(self.loc_id, inplace=True)
        

class CorrectionSet:
    def __init__(self, corrections: List[Correction]) -> None:
        self.corrections = corrections
        
    def apply(self, df: pd.DataFrame) -> None:
        for correction in self.corrections:
            correction.apply(df)
            
    def to_dict(self):
        corrections_dicts = [correction.to_dict() for correction in self.corrections]
        corrections_hash = get_hash(corrections_dicts)
        return {"corrections": corrections_dicts, "corrections_hash": corrections_hash}
    
    def to_json(self, fpath: str):
        with open(fpath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, d):
        corrections = []
        for correction_dict in d["corrections"]:
            classname = correction_dict.pop("class")
            class_ = globals()[classname]
            corrections.append(class_.from_dict(correction_dict))
        return cls(corrections)
    
    @classmethod
    def from_json(cls, fpath):
        with open(fpath) as f:
            return cls.from_dict(json.load(f))
            
            

   