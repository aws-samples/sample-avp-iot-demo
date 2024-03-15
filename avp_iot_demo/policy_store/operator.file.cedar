permit (
  principal in AVP::IoT::Demo::Role::"${operator_role_id}",
  action in
    [AVP::IoT::Demo::Action::"listFiles", AVP::IoT::Demo::Action::"getFile"],
  resource in AVP::IoT::Demo::File::"ALL"
);