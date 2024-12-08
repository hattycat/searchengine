class Posting:
    def __init__(self, doc_id, count, positions=None):
        self.count = count
        self.doc_id = doc_id
        self.positions = positions or [] 

    def __str__(self):
        return f"Posting(doc_id={self.doc_id}, count={self.count}, positions={self.positions})"

    def __repr__(self):
        return f"Posting(doc_id={self.doc_id}, count={self.count}, positions={self.positions})"