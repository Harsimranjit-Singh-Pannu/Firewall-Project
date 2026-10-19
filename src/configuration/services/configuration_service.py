class ConfigurationService:

    def __init__(
        self,
        draft_service
    ):

        self.draft_service = draft_service

    def get_configuration(
        self,
        draft_id
    ):

        draft = self.draft_service.get_draft(
            draft_id
        )

        if draft is None:

            raise ValueError(
                "Draft not found"
            )

        return draft.configuration

    def update_configuration(
        self,
        draft_id,
        configuration
    ):

        return self.draft_service.update_configuration(
            draft_id,
            configuration
        )

    def clear_changes(
        self,
        draft_id
    ):

        return self.draft_service.clear_changes(
            draft_id
        )

    
    def commit(
        self,
        draft_id,
        name,
        description=None,
    ):
        return self.draft_service.commit(
            draft_id,
            name=name,
            description=description,
        )