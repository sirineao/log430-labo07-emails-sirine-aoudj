"""
Kafka Historical User Event Consumer (Event Sourcing)
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import os
from logger import Logger
from typing import Optional
from kafka import KafkaConsumer
from handlers.handler_registry import HandlerRegistry

class UserEventHistoryConsumer:
    """A consumer that starts reading Kafka events from the earliest point from a given topic"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        registry: HandlerRegistry,
        output_dir: str = "output"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.registry = registry
        self.output_dir = output_dir
        self.auto_offset_reset = "earliest"
        self.consumer: Optional[KafkaConsumer] = None
        self.logger = Logger.get_instance("UserEventHistoryConsumer")
        os.makedirs(output_dir, exist_ok=True)
    
    def start(self) -> None:
        """Start consuming messages from Kafka"""
        self.logger.info(f"Démarrer un consommateur : {self.group_id}")
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=True,
                consumer_timeout_ms=5000
            )
            
            history_file = os.path.join(self.output_dir, "user_events_history.jsonl")
            
            with open(history_file, 'w', encoding='utf-8') as f:
                event_count = 0
                for message in self.consumer:
                    event_data = message.value
                    json_line = json.dumps(event_data, ensure_ascii=False)
                    f.write(json_line + '\n')
                    event_count += 1
                    self.logger.debug(f"Événement enregistré: {event_data.get('event')} (ID: {event_data.get('id')})")
            
            self.logger.info(f"Historique des événements enregistré dans {history_file}. Total: {event_count} événements.")
            
        except Exception as e:
            self.logger.error(f"Erreur: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the consumer gracefully"""
        if self.consumer:
            self.consumer.close()
            self.logger.info("Arrêter le consommateur!")