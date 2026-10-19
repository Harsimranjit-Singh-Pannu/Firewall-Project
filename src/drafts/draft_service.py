import copy

from drafts.draft import Draft


class DraftService:

    def __init__(
        self,
        repository,
        version_service
    ):

        self.repository = repository

        self.version_service = version_service

    def create_draft(
        self,
        version_id,
        configuration
    ):

        base_version = self.version_service.get_version(
            version_id
        )

        if base_version is None:

            raise ValueError(
                "Version not found"
            )

        draft = Draft(

            base_version_id=base_version.id,

            configuration=copy.deepcopy(
                configuration
            )

        )

        return self.repository.save(
            draft
        )

    def get_draft(
        self,
        draft_id
    ):

        return self.repository.get(
            draft_id
        )

    def list_drafts(
        self
    ):

        return self.repository.list()

    def update_configuration(
        self,
        draft_id,
        configuration
    ):

        draft = self.repository.get(
            draft_id
        )

        if draft is None:

            raise ValueError(
                "Draft not found"
            )

        draft.configuration = copy.deepcopy(
            configuration
        )

        return self.repository.save(
            draft
        )

    def clear_changes(
        self,
        draft_id
    ):

        draft = self.repository.get(
            draft_id
        )

        if draft is None:

            raise ValueError(
                "Draft not found"
            )

        self.repository.delete(
            draft_id
        )

        return True

    
    def commit(
        self,
        draft_id,
        name,
        description=None,
    ):
        draft = self.repository.get(
            draft_id
        )

        if draft is None:
            raise ValueError(
                "Draft not found"
            )

        version = self.version_service.create_version(
            configuration=draft.configuration,
            name=name,
            description=description,
            parent_version_id=draft.base_version_id,
        )

        self.repository.delete(
            draft_id
        )

        return version