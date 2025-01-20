const activePage = window.location.pathname;
const navLinks = document.querySelectorAll('.header-right-user a').forEach(link => {
  if(link.href.includes(`${activePage}`)){
    link.classList.add('active');
    console.log(link);
  }
})