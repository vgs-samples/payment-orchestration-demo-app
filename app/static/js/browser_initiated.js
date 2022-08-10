async function reloadFI(id) {
    let current_fi = document.getElementById('current-financial-instrument-info')
    current_fi.classList.add('loading')

    let fin_instr_request = await fetch(`/financial_instrument?id=${id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    });

    let fin_instr_response = await fin_instr_request.json()
    console.log(fin_instr_response.data)
    populateCurrentFinancialInstrument(fin_instr_response.data)

    current_fi.classList.remove('loading')
}

async function updateCurrentFI() {
    let selectorEl = document.getElementById('financial-instrument-selector')
    let id = selectorEl.value

    if(id) {
        await reloadFI(id)
    }
}

function rebuildFinancialInstrumentOptions(financial_instruments) {
    let currEls = document.getElementsByClassName('financial-instrument-option')
    for(let i=0; i<currEls.length; i++) {
        let el = currEls[i]
        delete el
    }
    let selectorEl = document.getElementById('financial-instrument-selector')
    
    for(let i=0; i<financial_instruments.length; i++) {
        let fi = financial_instruments[i]
        let newOption = new Option(`${fi.brand} ****${fi?.last4} - ${fi.id}`,fi.id);
        newOption.className = 'financial-instrument-option'
        if(i == financial_instruments.length - 1) {
            document.getElementById('financial-instrument-info').classList.remove('hidden')
            newOption.selected = true
            reloadFI(fi.id)
        }
        selectorEl.append(newOption)
    }
}

function addFinancialInstrument(data) {
    if (data?.id && data?.card?.brand) {
        financial_instruments = []
        if(localStorage.financial_instruments) {
            financial_instruments = JSON.parse(localStorage.financial_instruments)
        }
        
        financial_instruments.unshift({
            id: data.id,
            brand: data.card.brand,
            last4: data.card.last4
        })
        localStorage.setItem('financial_instruments', JSON.stringify(financial_instruments))
        rebuildFinancialInstrumentOptions(financial_instruments)
    }
}

function populateCurrentFinancialInstrument(data) {
    document.getElementById('financial-instrument-id').innerHTML = data?.id
    document.getElementById('financial-instrument-alias').innerHTML = data?.card?.number
    document.getElementById('financial-instrument-brand').innerHTML = data?.card?.brand
    document.getElementById('financial-instrument-address').innerHTML = data?.card?.billing_address?.address1
    document.getElementById('financial-instrument-zip').innerHTML = data?.card?.billing_address?.postal_code
    document.getElementById('financial-instrument-country').innerHTML = data?.card?.billing_address?.country
}

async function init() {
    document.getElementById('financial-instrument-selector').onchange = updateCurrentFI

    let STORED_FINANCIAL_INSTRUMENTS = localStorage.getItem('financial_instruments')
    if(STORED_FINANCIAL_INSTRUMENTS) {
        STORED_FINANCIAL_INSTRUMENTS = JSON.parse(STORED_FINANCIAL_INSTRUMENTS)
        rebuildFinancialInstrumentOptions(STORED_FINANCIAL_INSTRUMENTS)
    }

    let at_request = await fetch('/get_access_token', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    });

    let at_response = await at_request.json()

    console.log('Access Response', at_response)

    const checkout = new VGSCheckout.Checkout({
        vaultId: window.customerVaultId,
        environment: "sandbox",
        accessToken: at_response['access_token'],
        billingAddress: true
    });

    checkout.mount("#vgs-checkout", {
        labels: {
            submit: {
                ctaLabel: 'Store Card Data'
            }
        }
    });

    checkout.on('SubmitStart', ({ data }) => {
        checkout.update({
            formStatus: "loading"
        });
    })

    checkout.on('SubmitSuccess', ({ data }) => {
        console.log("Success", data)
        checkout.update({
            formStatus: "success"
        });
        addFinancialInstrument(data?.data)
    })

    checkout.on('SubmitFail', ({ data }) => {
        console.log("Failed", data)
        checkout.update({
            formStatus: "error"
        });
    })
    document.getElementById('gateway-options-editor').innerHTML = '{\n"device_id": "12345",\n"ip_address": "127.0.0.1",\n"email": "aceitei@getnet.com.br",\n"customer_id": "12345"\n}'
    
    document.getElementById('post-transfer').onclick = function() {
        document.getElementById('financial-instrument-info').classList.add('loading')
        let at_request = fetch('/transfer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                financial_instrument_id: document.getElementById('financial-instrument-selector').value,
                gateway_options: document.getElementById('gateway-options-editor').value,
                currency: document.getElementById('currency').value,
                amount: document.getElementById('amount').value
            })
        }).then((r) => {
            document.getElementById('financial-instrument-info').classList.remove('loading')
            r.json().then(data => {
                console.log(data)
                let el = document.getElementById('transfer-response-template').cloneNode(true)
                el.id = null
                let responses = document.getElementById('transfer-responses')
                if(data?.data?.state == "successful") {
                    el.classList.add('bg-green-200')
                }
                else {
                    el.classList.add('bg-red-200')
                }
                el.getElementsByClassName('response-gateway')[0].innerHTML = `Gateway ID: ${data?.data?.gateway?.id}`
                el.getElementsByClassName('response-psp')[0].innerHTML = `PSP: ${data?.data?.gateway?.type}`
                el.getElementsByClassName('response-message')[0].innerHTML = `${data?.data?.gateway_response?.message}`
                el.classList.remove('hidden')
                // Alwas add the new element to the beginning of the list of children.
                responses.children[0].insertAdjacentElement('beforebegin', el)
            })
            
        })
    }
}

init().then(
    console.log('Finished loading')
)