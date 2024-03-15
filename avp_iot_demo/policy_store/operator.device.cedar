permit (
  principal in AVP::IoT::Demo::Role::"${operator_role_id}",
  action in [AVP::IoT::Demo::Action::"listDevices"],
  resource in AVP::IoT::Demo::Device::"ALL"
);