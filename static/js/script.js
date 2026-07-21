// Welcome Message
console.log("Invoice Generator Loaded Successfully");

// Smooth Button Animation

const buttons = document.querySelectorAll(".btn");

buttons.forEach(btn => {

    btn.addEventListener("mouseenter", function(){

        this.style.transform = "scale(1.05)";

    });

    btn.addEventListener("mouseleave", function(){

        this.style.transform = "scale(1)";

    });

});