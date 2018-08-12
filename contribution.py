class Contribution():
    def __init__(self, row):
        self.moderator = row[0]
        self.review_date = row[1]
        self.url = row[2]
        self.repository = row[3]
        self.category = row[4]
        self.score = row[5]
        self.staff_pick = row[6]
        self.staff_pick_date = row[7]
        self.picked_by = row[8]
        self.review_status = row[9]
        self.vote_status = row[10]
        self.weight = row[11]
