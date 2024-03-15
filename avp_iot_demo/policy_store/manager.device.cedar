permit (
  principal in AVP::IoT::Demo::Role::"${manager_role_id}",
  action in
    [AVP::IoT::Demo::Action::"listDevices",
     AVP::IoT::Demo::Action::"updateDevice"],
  resource in AVP::IoT::Demo::Device::"ALL"
);