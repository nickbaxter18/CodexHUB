from src.monitor import MonitoringClient


def test_monitor_records_metrics():
    monitor = MonitoringClient()
    monitor.start_run()
    monitor.record_articles("news_api", 5)
    monitor.record_error("news_api", RuntimeError("boom"))
    monitor.record_document_upload()
    monitor.complete_run(status="success")

    snapshot = monitor.snapshot()
    assert snapshot.articles_processed == 5
    assert snapshot.errors == 1
    assert snapshot.source_counts["news_api"] == 5
    assert snapshot.documents_uploaded == 1
    assert snapshot.runs == 1
    metrics = monitor.metrics()
    assert metrics["last_status"] == "success"
    payload = monitor.render_prometheus()
    assert "gnds_articles_processed_total" in payload
