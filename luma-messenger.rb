cask "luma-messenger" do
  version "0.1.0"
  sha256 "REPLACE_WITH_SHA256_OF_THE_ZIP"

  url "https://github.com/Jimboo1865/luma-messenger/releases/download/v#{version}/Luma-Messenger-#{version}-macOS.zip"
  name "Luma Messenger"
  desc "Send templated iMessages to Luma event guests from a CSV"
  homepage "https://github.com/Jimboo1865/luma-messenger"

  app "Luma Messenger.app"
end
