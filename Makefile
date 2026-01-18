sync:
	./simplenote-sync.sh

run:
	PYTHONPATH=../simperium-python python3 simplenote-backup.py $(BACKUP_DIR)

import:
	PYTHONPATH=../simperium-python python3 simplenote-import.py $(IMPORT_DIR)

classify-list:
	python3 simplenote-classify.py list $(BACKUP_DIR)

classify-tags:
	python3 simplenote-classify.py tags $(BACKUP_DIR)

classify-json:
	python3 simplenote-classify.py json $(BACKUP_DIR)
