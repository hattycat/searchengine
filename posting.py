class Posting:
    def __init__(self, doc_id, count):
        self.count = count
        self.doc_id = doc_id

    def __str__(self):
        return f"Posting(doc_id={self.doc_id}, count={self.count}"

    def __repr__(self):
        return f"Posting(doc_id={self.doc_id}, count={self.count}"