function filter() {
    let rt = document.getElementById("routeFil");
    // let dest = document.getElementById("destFil");

    const hideClass = "hide"

    // filter rows if text input not empty
    let rows = document.querySelectorAll("tbody > *");
    if (rt.value) {
        let hideRow = 0;
        let hide = false;

        // iterate rows
        for (const row of rows) {
            let firstCell = row.children[0];

            // if first cell is a route cell,
            // get rowspan if exist, and hide/unhide rows
            if (firstCell.classList.contains("route")) {
                hide = !firstCell.innerHTML.toUpperCase().includes(rt.value.toUpperCase());
                console.log(hide)

                rowspan = firstCell.getAttribute("rowspan");
                if (rowspan) {
                    hideRow = parseInt(rowspan);
                } else {
                    hideRow = 1;
                }
            }

            // hide row(s)
            if (hideRow >= 1) {
                if (hide) {
                    row.classList.add(hideClass);
                    console.log("hide");
                } else {
                    row.classList.remove(hideClass);
                    console.log("unhide");
                }
                hideRow--;
            }
        }
    } else {
        // unhide all rows
        for (const row of rows) {
            row.classList.remove(hideClass);
            console.log("unhide");
        }
    }
}