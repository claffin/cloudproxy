import unittest
from unittest.mock import patch, MagicMock
import datetime
import dateparser

from cloudproxy.providers.digitalocean.main import (
    do_deployment,
    do_check_alive,
    do_check_delete,
    do_fw,
    do_start,
)
from cloudproxy.providers.digitalocean.functions import DOFirewallExistsException


class TestDigitalOceanMainCoverage(unittest.TestCase):

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_deploy_new(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 3}
        }
        mock_list_droplets.return_value = [MagicMock(), MagicMock()]  # 2 existing droplets

        do_deployment(3)

        self.assertEqual(mock_create_proxy.call_count, 1)  # Should create 1 new droplet
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_destroy_overprovisioned(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 1}
        }
        mock_list_droplets.return_value = [
            MagicMock(ip_address="1.1.1.1"),
            MagicMock(ip_address="2.2.2.2"),
        ]  # 2 existing droplets

        do_deployment(1)

        self.assertEqual(mock_delete_proxy.call_count, 1)  # Should delete 1 droplet
        mock_create_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_min_scaling_met(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 2}
        }
        mock_list_droplets.return_value = [
            MagicMock(),
            MagicMock(),
        ]  # 2 existing droplets

        do_deployment(2)

        mock_create_proxy.assert_not_called()
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.check_alive")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.dateparser.parse")
    @patch("cloudproxy.providers.digitalocean.main.datetime")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_alive_pending_droplet(
        self,
        mock_config,
        mock_datetime,
        mock_dateparser_parse,
        mock_delete_proxy,
        mock_check_alive,
        mock_list_droplets,
    ):
        mock_config["age_limit"] = 0
        mock_datetime.datetime.now.return_value = datetime.datetime(
            2023, 1, 1, 12, 5, 0, tzinfo=datetime.timezone.utc
        )
        mock_dateparser_parse.return_value = datetime.datetime(
            2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
        )  # 5 minutes old
        mock_list_droplets.return_value = [MagicMock(ip_address="1.1.1.1")]
        mock_check_alive.return_value = False
        mock_dateparser_parse.side_effect = TypeError # Simulate pending state

        ip_ready = do_check_alive()

        self.assertEqual(ip_ready, [])
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_in_delete_queue(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_delete_queue.append("1.1.1.1")
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]
        mock_delete_proxy.return_value = True

        do_check_delete()

        mock_delete_proxy.assert_called_once()
        self.assertNotIn("1.1.1.1", mock_delete_queue)

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_in_restart_queue(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_restart_queue.append("1.1.1.1")
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]
        mock_delete_proxy.return_value = True

        do_check_delete()

        mock_delete_proxy.assert_called_once()
        self.assertNotIn("1.1.1.1", mock_restart_queue)

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_not_in_queues(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]

        do_check_delete()

        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_no_droplets(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_list_droplets.return_value = []

        do_check_delete()

        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_fw_create_success(self, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }

        do_fw()

        mock_create_firewall.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_fw_firewall_exists(self, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }
        mock_create_firewall.side_effect = DOFirewallExistsException

        do_fw()

        mock_create_firewall.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.digitalocean.main.logger")
    def test_do_fw_other_exception(self, mock_logger, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }
        mock_create_firewall.side_effect = Exception("Some error")

        do_fw()

        mock_create_firewall.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.do_fw")
    @patch("cloudproxy.providers.digitalocean.main.do_check_delete")
    @patch("cloudproxy.providers.digitalocean.main.do_check_alive")
    @patch("cloudproxy.providers.digitalocean.main.do_deployment")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_start(
        self,
        mock_config,
        mock_do_deployment,
        mock_do_check_alive,
        mock_do_check_delete,
        mock_do_fw,
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 1}
        }
        mock_do_check_alive.side_effect = [[], ["1.1.1.1"]] # Simulate initial check and final check

        do_start()

        mock_do_fw.assert_called_once()
        mock_do_check_delete.assert_called_once()
        self.assertEqual(mock_do_check_alive.call_count, 2)
        mock_do_deployment.assert_called_once()


if __name__ == "__main__":
    unittest.main()