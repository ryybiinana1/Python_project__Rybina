def check_saving_path(path: str) -> bool:
    return bool(path)
def has_picture_amount_been_chosen(pictures_amount: int) -> bool:
    return bool(pictures_amount)
def is_picture_amount_positive_int(pictures_amount: int) -> bool:
    return pictures_amount > 0
def validate_picture_amount(pictures_amount: int,
                              links_array: set[str]) -> bool:
    return pictures_amount <= len(links_array)
