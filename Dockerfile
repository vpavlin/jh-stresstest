FROM centos/python-36-centos7

USER root
RUN echo -e "[google-chrome]\nname=google-chrome\nbaseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64\nenabled=1\ngpgcheck=1\ngpgkey=https://dl.google.com/linux/linux_signing_key.pub" > /etc/yum.repos.d/google-chrome.repo &&\
    yum -y install google-chrome-stable &&\
    yum clean all
USER 1001
RUN fix-permissions /opt/app-root