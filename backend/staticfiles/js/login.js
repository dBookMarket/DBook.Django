const loginWithMetamask = (login_url) => {
    requirejs(['/static/js/libs/web3.min.js'], function (Web3) {
        console.log($);
        const ethereum = window.ethereum;
        // check if install metamask
        if(typeof ethereum === 'undefined' || !ethereum.isMetaMask){
            alert('Metamask is not installed');
        }

        //
        // web3.eth.getAccounts().then(console.log);
        // connect to metamask
        ethereum.request({method: 'eth_requestAccounts'}).then(res => {
            console.log('aaaaaaaaa', res);
            const address = res[0];
            $.ajax({
                type: "POST",
                url: "/api/v1/nonce",
                data: {'address': address},
                success: data => {
                    console.log('ccccccc', data);
                    const {nonce} = data;
                    let web3 = new Web3(ethereum);
                    web3.eth.personal.sign(nonce, address).then(signature => {
                        $.ajax({
                            type: "POST",
                            url: `${login_url}`,
                            data: {
                                'address': address,
                                'signature': signature
                            },
                            beforeSend: (xhr, settings) => {
                              xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token }}");
                            },
                            success: data => {
                                console.log('success', data);
                            },
                            error: data => {
                                console.log('error', data);
                            }
                        })
                    })
                },
                error: response => {
                    console.log('eeeeeee', response);
                }
            })
        }).catch(err => {
            console.log('bbbbbbbbb', err);
        });

    })
}

