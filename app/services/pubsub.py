import json
import logging

from flask import current_app
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class PubSubService:
    def __init__(self):
        self._publisher = None

    @property
    def publisher(self):
        # Lazy load to avoid initialization issues outside application context
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def publish_upload_event(self, blob_name: str) -> bool:
        """Publish the required JSON payload to trigger the renaming worker."""
        project_id = current_app.config.get("PUBSUB_PROJECT_ID")
        topic_name = current_app.config.get("PUBSUB_TOPIC_NAME")

        if not project_id or not topic_name:
            logger.error("Pub/Sub project or topic missing from runtime config.")
            return False

        topic_path = self.publisher.topic_path(project_id, topic_name)
        message_data = json.dumps({"name": blob_name}).encode("utf-8")

        try:
            future = self.publisher.publish(topic_path, data=message_data)
            future.result()
            logger.info("Published upload event for blob: %s", blob_name)
            return True
        except Exception as exc:
            logger.exception("Pub/Sub publish failed for %s: %s", blob_name, exc)
            return False


pubsub_service = PubSubService()
