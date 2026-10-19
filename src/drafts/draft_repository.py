from uuid import UUID


class DraftRepository:

    def __init__(self):

        self.drafts = {}

    def save(
        self,
        draft
    ):

        self.drafts[draft.id] = draft

        return draft

    def get(
        self,
        draft_id
    ):

        if isinstance(
            draft_id,
            str
        ):

            try:

                draft_id = UUID(
                    draft_id
                )

            except ValueError:

                return None

        return self.drafts.get(
            draft_id
        )

    def list(
        self
    ):

        return list(
            self.drafts.values()
        )

    def delete(
        self,
        draft_id
    ):

        if isinstance(
            draft_id,
            str
        ):

            try:

                draft_id = UUID(
                    draft_id
                )

            except ValueError:

                return

        self.drafts.pop(
            draft_id,
            None
        )