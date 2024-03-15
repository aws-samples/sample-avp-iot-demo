permit (
  principal,
  action in [AVP::IoT::Demo::Action::"listRoleActions"],
  resource in AVP::IoT::Demo::Role::"ALL"
)
when { principal == resource };