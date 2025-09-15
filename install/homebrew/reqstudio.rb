class Reqstudio < Formula
  include Language::Python::Virtualenv

  desc "Git-driven requirements/SRS editor (PyQt6)"
  homepage "https://y10k-tech.github.io/reqstudio/"
  url "https://github.com/YOUR_ORG/reqstudio/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.11"

  resource "PyQt6" do
    url "https://files.pythonhosted.org/packages/.../PyQt6.whl"
    sha256 "SKIP_OR_FILL"
  end

  # Optional: add other python resources explicitly, or rely on pip to resolve within venv

  def install
    virtualenv_install_with_resources
    # Create a launcher script in bin
    (bin/"reqstudio").write <<~EOS
      #!/bin/bash
      VENV="#{libexec}/bin"
      exec "$VENV/python" "#{libexec}/app.py" "$@"
    EOS
    chmod 0755, bin/"reqstudio"
  end

  def caveats
    <<~EOS
      ReqStudio installed into a Python virtualenv.
      Launch with: reqstudio
    EOS
  end
end
